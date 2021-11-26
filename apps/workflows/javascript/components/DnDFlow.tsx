import React, { useState, useRef, useEffect } from 'react'
import ReactDOM from 'react-dom'

import ReactFlow, {
  Controls,
  Edge,
  Node,
  useZoomPanHelper,
  Background,
  ConnectionLineType,
} from 'react-flow-renderer'
import LayoutButton from './LayoutButton'
import defaultNodeTypes from './Nodes'
import RunButton from './RunButton'

import '../styles/_dnd-flow.scss'
import { DnDContext } from '../context'
import { getWorkflowStatus, listAll } from '../actions'
import { toEdge, toNode } from '../serde'
import ZeroState from './ZeroState'
import ErrorState from './ErrorState'
import LoadingState from './LoadingState'
import useDnDActions from '../hooks/useDnDActions'

const GRID_GAP = 20

enum LoadingStates {
  loading,
  loaded,
  failed,
}

const DnDFlow = ({ workflowId }) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const { fitView } = useZoomPanHelper()

  const [elements, setElements] = useState<(Edge | Node)[]>([])
  const [initialLoad, setInitialLoad] = useState(LoadingStates.loading)
  const [hasBeenRun, setHasBeenRun] = useState(false)
  const [isOutOfDate, setIsOutOfDate] = useState(false)
  const [needsFitView, setNeedsFitView] = useState(false)

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
        setNeedsFitView(true)
        setInitialLoad(LoadingStates.loaded)
      } catch {
        setInitialLoad(LoadingStates.failed)
      }
    }

    syncElements()
  }, [])

  useEffect(() => {
    if (needsFitView) {
      fitView()
      setNeedsFitView(false)
    }
  }, [needsFitView])

  useEffect(() => {
    getWorkflowStatus(workflowId).then((res) => {
      setHasBeenRun(res.hasBeenRun)
      setIsOutOfDate(res.isOutOfDate)
    })
  }, [])

  return (
    <DnDContext.Provider
      value={{
        workflowId,
        elements,
        setElements,
        hasBeenRun,
        setHasBeenRun,
        isOutOfDate,
        setIsOutOfDate,
        setNeedsFitView,
        removeById: (id: string) => {
          const elemenToRemove = elements.filter((el) => el.id === id)
          onElementsRemove(elemenToRemove)
        },
        addNode: (data) => {
          const node = toNode(data, { x: data.x, y: data.y })
          const edges = data.parents.map((parent) => toEdge(node, parent))
          setElements((es) => es.concat(node, edges))
        },
      }}
    >
      <div className='reactflow-wrapper' ref={reactFlowWrapper}>
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
            <LayoutButton />
          </Controls>
          <Background gap={GRID_GAP} />
          {(needsFitView || initialLoad === LoadingStates.loading) && <LoadingState />}
          {initialLoad === LoadingStates.failed && (
            <ErrorState error='Failed loading your nodes!' />
          )}
          {initialLoad === LoadingStates.loaded && elements.length === 0 && <ZeroState />}
        </ReactFlow>
      </div>

      {ReactDOM.createPortal(
        <RunButton />,
        document.getElementById('run-button-portal') as HTMLDivElement
      )}
    </DnDContext.Provider>
  )
}

export default DnDFlow
