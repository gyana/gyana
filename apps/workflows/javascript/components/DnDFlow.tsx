import React, { useState, useRef, useEffect } from 'react'
import ReactDOM from 'react-dom'

import ReactFlow, {
  Controls,
  isNode,
  Edge,
  Node,
  getIncomers,
  useZoomPanHelper,
  Background,
  ConnectionLineType,
} from 'react-flow-renderer'
import LayoutButton from './LayoutButton'
import defaultNodeTypes from './Nodes'
import RunButton from './RunButton'

import '../styles/_dnd-flow.scss'
import { NodeContext } from '../context'
import { getWorkflowStatus, listAll } from '../actions'
import { toEdge, toNode } from '../serde'
import ZeroState from './ZeroState'
import ErrorState from './ErrorState'
import LoadingState from './LoadingState'
import useDnDActions from '../hooks/useDnDActions'
import { getIncomingNodes } from '../edges'

const GRID_GAP = 20

enum LoadingStates {
  loading,
  loaded,
  failed,
}

const DnDFlow = ({ workflowId }) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const [elements, setElements] = useState<(Edge | Node)[]>([])
  const { fitView } = useZoomPanHelper()
  const [isOutOfDate, setIsOutOfDate] = useState(false)
  const [hasBeenRun, setHasBeenRun] = useState(false)
  // State whether the initial element load has been done
  const [initialLoad, setInitialLoad] = useState(LoadingStates.loading)
  const [viewHasChanged, setViewHasChanged] = useState(false)

  const setElementsDirty = (updater) => {
    setElements(updater)
    setIsOutOfDate(true)
  }

  const { onLoad, onDragOver, onDrop, onNodeDragStop, onConnect, onEdgeUpdate, onElementsRemove } =
    useDnDActions(workflowId, reactFlowWrapper, elements, setElementsDirty)

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

  return (
    <>
      <div className='reactflow-wrapper' ref={reactFlowWrapper}>
        <NodeContext.Provider
          value={{
            removeById: (id: string) => {
              const elemenToRemove = elements.filter((el) => el.id === id)
              onElementsRemove(elemenToRemove)
            },
            addNode: (data) => {
              const node = toNode(data, { x: data.x, y: data.y })
              const edges = data.parents.map((parent) => toEdge(node, parent))
              setElements((es) => es.concat(node, edges))
            },
            getIncomingNodes: (target: string) => getIncomingNodes(elements, target),
            workflowId,
          }}
        >
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
        document.getElementById('run-button-portal') as HTMLDivElement
      )}
    </>
  )
}

export default DnDFlow
