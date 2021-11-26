import React, { useState, useRef, useEffect } from 'react'
import ReactDOM from 'react-dom'

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
import { INode } from '../interfaces'
import LayoutButton from './LayoutButton'
import defaultNodeTypes from './Nodes'
import RunButton from './RunButton'
import { getApiClient } from 'apps/base/javascript/api'

const client = getApiClient()

import '../styles/_dnd-flow.scss'
import { NodeContext } from '../context'
import {
  createNode,
  deleteNode,
  getWorkflowStatus,
  listAll,
  moveNode,
  updateParentEdges,
} from '../actions'
import { toEdge, toNode } from '../serde'

const NODES = JSON.parse(document.getElementById('nodes').textContent) as INode
const GRID_GAP = 20

enum LoadingStates {
  loading,
  loaded,
  failed,
}

const DnDFlow = ({ workflowId }) => {
  const runButtonPortal = document.getElementById('run-button-portal')
  const reactFlowWrapper = useRef(null)
  const [reactFlowInstance, setReactFlowInstance] = useState(null)
  const [elements, setElements] = useState<(Edge | Node)[]>([])
  const { fitView } = useZoomPanHelper()
  const [isOutOfDate, setIsOutOfDate] = useState(false)
  const [hasBeenRun, setHasBeenRun] = useState(false)
  // State whether the initial element load has been done
  const [initialLoad, setInitialLoad] = useState(LoadingStates.loading)
  const [viewHasChanged, setViewHasChanged] = useState(false)

  const getIncomingNodes = (target: string) => {
    const targetElement = elements.filter((el) => isNode(el) && el.id === target)[0] as
      | Node
      | undefined
    return targetElement
      ? ([targetElement, getIncomers(targetElement, elements)] as [Node, Node[]])
      : null
  }

  const onConnect = (params) => {
    const [targetElement, incomingNodes] = getIncomingNodes(params.target)

    // All nodes except Join (2) and Union (inf) can only have one parent
    const maxParents = NODES[targetElement.data.kind].maxParents
    if (maxParents === -1 || incomingNodes.length < maxParents) {
      const parents = elements
        .filter((el) => isEdge(el) && el.target === params.target)
        .map((el) => el.source)

      updateParentEdges(params.target, [...parents, params.source])
      setElements((els) =>
        addEdge({ ...params, arrowHeadType: 'arrowclosed', type: 'smoothstep' }, els)
      )
    }
  }

  const onElementsRemove = (elementsToRemove) => {
    setElements((els) => removeElements(elementsToRemove, els))
    elementsToRemove.forEach((el) => {
      if (isNode(el)) {
        deleteNode(el)
      } else {
        const parents = elements
          .filter(
            (currEl) =>
              isEdge(currEl) && currEl.target === edge.target && currEl.source !== edge.source
          )
          .map((currEl) => currEl.source)

        updateParentEdges(edge.target, parents)
      }
    })
    setIsOutOfDate(true)
  }

  const onEdgeUpdate = (oldEdge: Edge, newEdge: Edge) => {
    // User changed the target
    if (oldEdge.source === newEdge.source) {
      // We need to remove the source from the previous target and
      // add it to the new one

      const [targetElement, incomingNodes] = getIncomingNodes(newEdge.target)
      // All nodes except Join (2) and Union (inf) can only have one parent
      const maxParents = NODES[targetElement.data.kind].maxParents || 1

      if (maxParents === -1 || incomingNodes.length < maxParents) {
        const oldParents = elements
          .filter(
            (el) => isEdge(el) && el.target === oldEdge.target && el.source !== oldEdge.source
          )
          .map((el) => el.source)
        updateParentEdges(oldEdge.target, oldParents)

        const newParents = elements
          .filter((el) => isEdge(el) && el.target === newEdge.target)
          .map((el) => el.source)

        updateParentEdges(newEdge.target, [...newParents, newEdge.source])
        setElements((els) => updateEdge(oldEdge, newEdge, els))
      }
    }
    // User changed the source
    else {
      // We only need to replace to old source with the new
      const parents = elements
        .filter((el) => isEdge(el) && el.target === oldEdge.target && el.source !== oldEdge.source)
        .map((el) => el.source)

      updateParentEdges(newEdge.target, [...parents, newEdge.source])
      setElements((els) => updateEdge(oldEdge, newEdge, els))
    }
    setIsOutOfDate(true)
  }

  const removeById = (id: string) => {
    const elemenToRemove = elements.filter((el) => el.id === id)
    onElementsRemove(elemenToRemove)
  }

  const getPosition = (event) => {
    const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect()
    return reactFlowInstance.project({
      x: event.clientX - reactFlowBounds.left,
      y: event.clientY - reactFlowBounds.top,
    })
  }

  const syncElements = async () => {
    try {
      const [nodes, edges] = await listAll(workflowId)
      setElements([...nodes, ...edges])
      setViewHasChanged(true)
      setInitialLoad(LoadingStates.loaded)
    } catch {
      setInitialLoad(LoadingStates.failed)
    }
  }

  useEffect(() => {
    syncElements()

    getWorkflowStatus(workflowId).then((res) => {
      setHasBeenRun(res.hasBeenRun)
      setIsOutOfDate(res.isOutOfDate)
    })
  }, [])

  useEffect(() => {
    if (viewHasChanged) {
      fitView()
      setViewHasChanged(false)
    }
  }, [viewHasChanged])

  const onDrop = async (event) => {
    event.preventDefault()
    const type = event.dataTransfer.getData('application/reactflow')
    const position = getPosition(event)
    const newNode = await createNode(workflowId, type, position)
    setElements((es) => es.concat(newNode))
    setIsOutOfDate(true)
  }

  const hasOutput = elements.some((el) => el.type === 'output')
  const addNode = (data) => {
    const node = toNode(data, { x: data.x, y: data.y })
    const edges = data.parents.map((parent) => toEdge(node, parent))
    setElements((es) => es.concat(node, edges))
  }

  return (
    <div className='reactflow-wrapper' ref={reactFlowWrapper}>
      <NodeContext.Provider value={{ removeById, client, getIncomingNodes, addNode, workflowId }}>
        <ReactFlow
          nodeTypes={defaultNodeTypes}
          elements={elements}
          connectionLineType={ConnectionLineType.SmoothStep}
          onConnect={onConnect}
          onElementsRemove={onElementsRemove}
          onEdgeUpdate={onEdgeUpdate}
          onLoad={(instance) => setReactFlowInstance(instance)}
          onDrop={onDrop}
          onDragOver={(event) => {
            event.preventDefault()
            event.dataTransfer.dropEffect = 'move'
          }}
          onNodeDragStop={(event, node) => moveNode(node)}
          snapToGrid={true}
          snapGrid={[GRID_GAP, GRID_GAP]}
          maxZoom={2}
          minZoom={0.05}
        >
          <Controls>
            <LayoutButton
              elements={elements}
              setElements={setElements}
              setViewHasChanged={setViewHasChanged}
              workflowId={workflowId}
            />
          </Controls>
          <Background gap={GRID_GAP} />

          {ReactDOM.createPortal(
            <RunButton
              hasOutput={hasOutput}
              hasBeenRun={hasBeenRun}
              setHasBeenRun={setHasBeenRun}
              workflowId={workflowId}
              elements={elements}
              setElements={setElements}
              isOutOfDate={isOutOfDate}
              setIsOutOfDate={setIsOutOfDate}
            />,
            runButtonPortal
          )}

          {(viewHasChanged || initialLoad === LoadingStates.loading) && (
            <div className='placeholder-scr placeholder-scr--fillscreen'>
              <i className='placeholder-scr__icon fad fa-spinner-third fa-spin fa-2x'></i>
              Loading...
            </div>
          )}
          {initialLoad === LoadingStates.failed && (
            <div className='placeholder-scr placeholder-scr--fillscreen'>
              <i className='fa fa-exclamation-triangle text-red fa-4x mb-3'></i>
              <p>Failed loading your nodes!</p>
              <p>
                Contact{' '}
                <a className='link' href='mailto: support@gyana.com'>
                  support@gyana.com
                </a>{' '}
                for support.
              </p>
            </div>
          )}
          {initialLoad === LoadingStates.loaded && elements.length === 0 && (
            <div className='placeholder-scr placeholder-scr--fillscreen gap-10'>
              <div className='flex items-center max-w-lg gap-7'>
                <i className={`fas fa-fw ${NODES['input'].icon} text-green fa-2x`}></i>
                <p>
                  Start building your workflow by dragging in a <strong>Get data</strong> node
                </p>
              </div>

              <div className='flex items-center max-w-lg gap-7'>
                <i className={`fas fa-fw ${NODES['filter'].icon} text-blue fa-2x`}></i>
                <p>
                  Drag and connect other <strong>Transformation</strong> nodes to clean and filter
                  your data
                </p>
              </div>

              <div className='flex items-center max-w-lg gap-7'>
                <i className={`fas fa-fw ${NODES['output'].icon} text-pink fa-2x`}></i>
                <p>
                  Once you are happy with your results, drag in a <strong>Save Data</strong> node
                  and name it
                </p>
              </div>

              <div className='flex items-center max-w-lg gap-7'>
                <i className={`fas fa-fw fa-play-circle text-green fa-2x`}></i>
                <p>
                  Press <strong>Run</strong> in the top right to create the new data source
                </p>
              </div>
            </div>
          )}
        </ReactFlow>
      </NodeContext.Provider>
    </div>
  )
}

export default DnDFlow
