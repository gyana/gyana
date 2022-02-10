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

import 'apps/base/javascript/styles/_react-flow.scss'
import { DnDContext } from '../context'
import { duplicateNode, getWorkflowStatus, listAll } from '../api'
import ZeroState from './ZeroState'
import ErrorState from 'apps/base/javascript/components/ErrorState'
import LoadingState from 'apps/base/javascript/components/LoadingState'
import Status from 'apps/base/javascript/components/Status'
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
  const [errors, setErrors] = useState({})
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
    async function workflowStatus() {
      await getWorkflowStatus(workflowId).then((res) => {
        console.log(res)
        setHasBeenRun(res.hasBeenRun)
        setIsOutOfDate(res.isOutOfDate)
        setErrors(res.errors)
      })
    }

    workflowStatus()
  }, [])

  return (
    <DnDContext.Provider
      value={{
        workflowId,
        elements,
        setElements,
        hasBeenRun,
        setHasBeenRun,
        errors,
        setErrors,
        isOutOfDate,
        setIsOutOfDate,
        setNeedsFitView,
        deleteNodeById: (id: string) => {
          const elemenToRemove = elements.filter((el) => el.id === id)
          onElementsRemove(elemenToRemove)
        },
        duplicateNodeById: async (id: string) => {
          const [node, edges] = await duplicateNode(id)
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
          {initialLoad === LoadingStates.loaded && <Status hasBeenRun={hasBeenRun} isOutOfDate={isOutOfDate} errors={errors} />}
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
