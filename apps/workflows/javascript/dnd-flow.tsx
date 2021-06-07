import React, { useState, useRef, useEffect } from 'react'

import ReactFlow, {
  addEdge,
  removeElements,
  Controls,
  updateEdge,
  isNode,
  Edge,
  Node,
  isEdge,
  getIncomers,
  useZoomPanHelper,
  Background,
  ConnectionLineType,
} from 'react-flow-renderer'
import { INode } from './interfaces'
import defaultNodeTypes, { NodeContext } from './Nodes'
import RunButton from './RunButton'

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
  const [isOutOfDate, setIsOutOfDate] = useState(false)
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

      updateParents(params.target, [...parents, params.source])
      setElements((els) => addEdge({ ...params, arrowHeadType: 'arrow', type: 'smoothstep' }, els))
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
    setIsOutOfDate(true)
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
    setIsOutOfDate(true)
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
    syncElements()

    client
      .action(window.schema, ['workflows', 'out_of_date', 'list'], { id: workflowId })
      .then((res) => setIsOutOfDate(res.isOutOfDate))
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
    setIsOutOfDate(true)
  }

  const hasOutput = elements.some((el) => el.type === 'output')

  return (
    <div className='dndflow'>
      <div className='reactflow-wrapper' ref={reactFlowWrapper}>
        <NodeContext.Provider value={{ removeById, client }}>
          <ReactFlow
            nodeTypes={defaultNodeTypes}
            elements={elements}
            connectionLineType={ConnectionLineType.SmoothStep}
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
            <RunButton
              hasOutput={hasOutput}
              client={client}
              workflowId={workflowId}
              elements={elements}
              setElements={setElements}
              isOutOfDate={isOutOfDate}
              setIsOutOfDate={setIsOutOfDate}
            />
          </ReactFlow>
        </NodeContext.Provider>
      </div>
      <Sidebar />
    </div>
  )
}

export default DnDFlow
