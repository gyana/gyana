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
  OnLoadParams,
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
import ZeroState from './ZeroState'
import ErrorState from './ErrorState'
import LoadingState from './LoadingState'
import {
  addEdgeToParents,
  canAddEdge,
  removeEdgeFromParents,
  updateEdgeSourceInParents,
  updateEdgeTargetInParents,
} from '../edges'

const GRID_GAP = 20

enum LoadingStates {
  loading,
  loaded,
  failed,
}

const DnDFlow = ({ workflowId }) => {
  const runButtonPortal = document.getElementById('run-button-portal')
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const [reactFlowInstance, setReactFlowInstance] = useState<OnLoadParams>()
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

  const onLoad = (instance) => setReactFlowInstance(instance)

  const onDragOver = (event) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }

  const onDrop = async (event: DragEvent) => {
    event.preventDefault()
    const { dataTransfer, clientX, clientY } = event

    if (
      reactFlowWrapper.current !== null &&
      reactFlowInstance !== undefined &&
      dataTransfer !== null
    ) {
      const type = dataTransfer.getData('application/reactflow')
      const { left, top } = reactFlowWrapper.current.getBoundingClientRect()
      const position = reactFlowInstance.project({
        x: clientX - left,
        y: clientY - top,
      })
      const newNode = await createNode(workflowId, type, position)
      setElements((es) => es.concat(newNode))
      setIsOutOfDate(true)
    }
  }

  const onNodeDragStop = (event, node) => moveNode(node)

  const onConnect = (params) => {
    if (canAddEdge(elements, params.target)) {
      updateParentEdges(params.target, addEdgeToParents(elements, params.source, params.target))
      setElements((els) =>
        addEdge({ ...params, arrowHeadType: 'arrowclosed', type: 'smoothstep' }, els)
      )
    }
  }

  const onEdgeUpdate = (oldEdge: Edge, newEdge: Edge) => {
    // Update the target of the edge
    if (oldEdge.source === newEdge.source) {
      if (canAddEdge(elements, newEdge.target)) {
        const [oldParents, newParents] = updateEdgeTargetInParents(elements, oldEdge, newEdge)
        updateParentEdges(oldEdge.target, oldParents)
        updateParentEdges(newEdge.target, newParents)
        setElements((els) => updateEdge(oldEdge, newEdge, els))
      }
    }
    // Update the source of the edge
    else {
      updateParentEdges(newEdge.target, updateEdgeSourceInParents(elements, oldEdge, newEdge))
      setElements((els) => updateEdge(oldEdge, newEdge, els))
    }
    setIsOutOfDate(true)
  }

  const onElementsRemove = (elementsToRemove) => {
    setElements((els) => removeElements(elementsToRemove, els))
    elementsToRemove.forEach((el) => {
      if (isNode(el)) {
        deleteNode(el)
      } else {
        updateParentEdges(el.target, removeEdgeFromParents(elements, el))
      }
    })
    setIsOutOfDate(true)
  }

  useEffect(() => {
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

    syncElements()
  }, [])

  useEffect(() => {
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

  const nodeContext = {
    removeById: (id: string) => {
      const elemenToRemove = elements.filter((el) => el.id === id)
      onElementsRemove(elemenToRemove)
    },
    addNode: (data) => {
      const node = toNode(data, { x: data.x, y: data.y })
      const edges = data.parents.map((parent) => toEdge(node, parent))
      setElements((es) => es.concat(node, edges))
    },
    getIncomingNodes,
    workflowId,
  }

  return (
    <>
      <div className='reactflow-wrapper' ref={reactFlowWrapper}>
        <NodeContext.Provider value={nodeContext}>
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
            onNodeDragStop={onNodeDragStop}
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
            {(viewHasChanged || initialLoad === LoadingStates.loading) && <LoadingState />}
            {initialLoad === LoadingStates.failed && (
              <ErrorState error='Failed loading your nodes!' />
            )}
            {initialLoad === LoadingStates.loaded && elements.length === 0 && <ZeroState />}
          </ReactFlow>
        </NodeContext.Provider>
      </div>

      {ReactDOM.createPortal(
        <RunButton
          hasOutput={elements.some((el) => el.type === 'output')}
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
    </>
  )
}

export default DnDFlow
