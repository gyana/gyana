import React, {
  useState,
  useRef,
  useEffect,
  createContext,
  useContext,
} from "react";

import ReactFlow, {
  addEdge,
  removeElements,
  Controls,
  Handle,
  NodeProps,
  Position,
  updateEdge,
  isNode,
  Edge,
  Node,
  isEdge,
  getIncomers,
  useZoomPanHelper,
  Background,
} from 'react-flow-renderer'
import { INode } from './interfaces'

import Sidebar from './sidebar'

import './styles/_dnd-flow.scss'
import './styles/_react-flow.scss'

const NODES = JSON.parse(document.getElementById('nodes').textContent) as INode
const GRID_GAP = 20

const DnDFlow = ({ client }) => {
  const reactFlowWrapper = useRef(null)
  const [reactFlowInstance, setReactFlowInstance] = useState(null)
  const [elements, setElements] = useState<(Edge | Node)[]>([])
  const { fitView } = useZoomPanHelper()

  // State whether the initial element load has been done
  const [initialLoad, setInitialLoad] = useState(false)

  // TODO: Make more robust to url changes
  const workflowId = window.location.pathname.split('/')[4]

  const updateParents = (id: string, parents: string[]) =>
    client.action(window.schema, ['workflows', 'api', 'nodes', 'partial_update'], {
      id,
      parents,
    })

  const getIncomingNodes = (target: string) => {
    const targetElement = elements.filter((el) => isNode(el) && el.id === target)[0] as Node
    return [targetElement, getIncomers(targetElement, elements)] as [Node, Node[]]
  }

  const onConnect = (params) => {
    const [targetElement, incomingNodes] = getIncomingNodes(params.target)

    // All nodes except Join (2) and Union (inf) can only have one parent
    const maxParents = NODES[targetElement.data.label].maxParents || 1
    if (maxParents === -1 || incomingNodes.length < maxParents) {
      const parents = elements
        .filter((el) => isEdge(el) && el.target === params.target)
        .map((el) => el.source)

      updateParents(params.target, [...parents, params.source]);
      setElements((els) => addEdge({ ...params, arrowHeadType: "arrow", type: "smoothstep" }, els))
    }
  }

  const onElementsRemove = (elementsToRemove) => {
    setElements((els) => removeElements(elementsToRemove, els))
    elementsToRemove.forEach((el) => {
      if (isNode(el)) {
        client.action(window.schema, ['workflows', 'api', 'nodes', 'delete'], {
          id: el.id,
        })
      } else {
        const parents = elements
          .filter(
            (currEl) => isEdge(currEl) && currEl.target === el.target && currEl.source !== el.source
          )
          .map((currEl) => currEl.source)

        updateParents(el.target, parents)
      }
    })
  }

  const onEdgeUpdate = (oldEdge, newEdge) => {
    // User changed the target
    if (oldEdge.source === newEdge.source) {
      // We need to remove the source from the previous target and
      // add it to the new one

      const [targetElement, incomingNodes] = getIncomingNodes(newEdge.target)

      // All nodes except Join (2) and Union (inf) can only have one parent
      const maxParents = NODES[targetElement.data.label].maxParents || 1

      if (maxParents === -1 || incomingNodes.length < maxParents) {
        const oldParents = elements
          .filter(
            (el) => isEdge(el) && el.target === oldEdge.target && el.source !== oldEdge.source
          )
          .map((el) => el.source)
        updateParents(oldEdge.target, oldParents)

        const newParents = elements
          .filter((el) => isEdge(el) && el.target === newEdge.target)
          .map((el) => el.source)

        updateParents(newEdge.target, [...newParents, newEdge.source])
        setElements((els) => updateEdge(oldEdge, newEdge, els))
      }
    }
    // User changed the source
    else {
      // We only need to replace to old source with the new
      const parents = elements
        .filter((el) => isEdge(el) && el.target === oldEdge.target && el.source !== oldEdge.source)
        .map((el) => el.source)

      updateParents(newEdge.target, [...parents, newEdge.source])
      setElements((els) => updateEdge(oldEdge, newEdge, els))
    }
  }

  const removeById = (id: string) => {
    const elemenToRemove = elements.filter((el) => el.id === id)
    onElementsRemove(elemenToRemove)
  }

  const onLoad = (_reactFlowInstance) => setReactFlowInstance(_reactFlowInstance)

  const onDragOver = (event) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }

  const getPosition = (event) => {
    const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect()
    return reactFlowInstance.project({
      x: event.clientX - reactFlowBounds.left,
      y: event.clientY - reactFlowBounds.top,
    })
  }

  const onDragStop = (event, node) => {
    const { position } = node

    client.action(window.schema, ['workflows', 'api', 'nodes', 'partial_update'], {
      id: node.id,
      x: position.x,
      y: position.y,
    })
  }

  const syncElements = () =>
    client
      .action(window.schema, ['workflows', 'api', 'nodes', 'list'], {
        workflow: workflowId,
      })
      .then((result) => {
        const newElements = result.results.map((r) => {
          return {
            id: `${r.id}`,
            type: ['input', 'output'].includes(r.kind) ? r.kind : 'default',
            data: { label: r.kind, description: r.description, error: r.error },
            position: { x: r.x, y: r.y },
          }
        })

        const edges = result.results
          .filter((r) => r.parents.length)
          .reduce((acc, curr) => {
            return [
              ...acc,
              ...curr.parents.map((p) => ({
                id: `reactflow__edge-${p}null-${curr.id}null`,
                source: p.toString(),
                sourceHandle: null,
                type: 'smoothstep',
                targetHandle: null,
                arrowHeadType: 'arrow',
                target: curr.id.toString(),
              })),
            ]
          }, [])
        setElements([...newElements, ...edges])
        setInitialLoad(true)
      })

  useEffect(() => {
    // Add event listener to show errors
    const eventName = `workflow-run-${workflowId}`
    window.addEventListener(eventName, syncElements, false)

    syncElements()
    // Cleanup event listener
    return () => window.removeEventListener(eventName, syncElements)
  }, [])

  useEffect(() => {
    fitView()
  }, [initialLoad])

  const onDrop = async (event) => {
    event.preventDefault()
    const type = event.dataTransfer.getData('application/reactflow')
    const position = getPosition(event)

    const result = await client.action(window.schema, ['workflows', 'api', 'nodes', 'create'], {
      kind: type,
      workflow: workflowId,
      x: position.x,
      y: position.y,
    })

    const newNode = {
      id: `${result.id}`,
      type: ['input', 'output'].includes(type) ? type : 'default',
      data: { label: result.kind },
      position,
    }

    setElements((es) => es.concat(newNode))
  }

  return (
    <div className='dndflow'>
      <div className='reactflow-wrapper' ref={reactFlowWrapper}>
        <NodeContext.Provider value={{ removeById, client }}>
          <ReactFlow
            nodeTypes={defaultNodeTypes}
            elements={elements}
            onConnect={onConnect}
            onElementsRemove={onElementsRemove}
            onEdgeUpdate={onEdgeUpdate}
            onLoad={onLoad}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeDragStop={onDragStop}
            snapToGrid={true}
            snapGrid={[GRID_GAP, GRID_GAP]}
          >
            <Controls />
            <Background gap={GRID_GAP} />
          </ReactFlow>
        </NodeContext.Provider>
      </div>
      <Sidebar />
    </div>
  )
}

const DeleteButton = ({ id }) => {
  const { removeById } = useContext(NodeContext)
  return (
    <button onClick={() => removeById(id)}>
      <i className='fas fa-trash fa-lg'></i>
    </button>
  )
}

const OpenButton = ({ id }) => {
  const workflowId = window.location.pathname.split('/')[4]

  return (
    <button data-action='click->tf-modal#open'>
      <i data-src={`/workflows/${workflowId}/nodes/${id}`} className='fas fa-cog fa-lg'></i>
    </button>
  )
}

const Description = ({ id, data }) => {
  const { client } = useContext(NodeContext)
  const workflowId = window.location.pathname.split('/')[4]

  const [description, setDescription] = useState()

  const onNodeConfigUpdate = async () => {
    const result = await client.action(window.schema, ['workflows', 'api', 'nodes', 'read'], {
      workflow: workflowId,
      id,
    })

    setDescription(result.description)
  }

  useEffect(() => {
    const eventName = `node-updated-${id}`
    window.addEventListener(eventName, onNodeConfigUpdate, false)
    return () => window.removeEventListener(eventName, onNodeConfigUpdate)
  }, [])

  return (
    <p className="overflow-ellipsis">
      {description || data.description}
    </p>
  );
};

const Buttons = ({ id }) => {
  return (
    <div className="react-flow__buttons">
      <OpenButton id={id} />
      <DeleteButton id={id} />
    </div>
  )
}

const ErrorIcon = ({ text }) => (
  <div
    title={text}
    className='flex items-center justify-around absolute -top-2 -right-2 bg-red-10 rounded-full w-6 h-6 text-red'
  >
    <i className='fad fa-bug '></i>
  </div>
)

const InputNode = ({ id, data, isConnectable, selected }: NodeProps) => (
  <>
    {selected && <Buttons id={id} />}
    {data.error && <ErrorIcon text={data.error} />}
    <h3>{data.label}</h3>
    <Description id={id} data={data} />

    <Handle
      type="source"
      position={Position.Right}
      isConnectable={isConnectable}
    />
  </>
)

const DefaultNode = ({
  id,
  data,
  isConnectable,
  targetPosition = Position.Left,
  sourcePosition = Position.Right,
  selected,
}: NodeProps) => {
  return (
    <>
      {selected && <Buttons id={id} />}
      {data.error && <ErrorIcon text={data.error} />}
      <Handle type='target' position={targetPosition} isConnectable={isConnectable} />
      <div className='flex flex-col h-full justify-center'>
        {data.label}
        <Description id={id} data={data} />
      </div>
      <Handle type='source' position={sourcePosition} isConnectable={isConnectable} />
    </>
  )
}

const defaultNodeTypes = {
  input: InputNode,
  output: OutputNode,
  default: DefaultNode,
}

const NodeContext = createContext({
  removeById: (id: string) => {},
  client: null,
})

export default DnDFlow
