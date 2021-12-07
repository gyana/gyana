import ErrorState from 'apps/workflows/javascript/components/ErrorState'
import LoadingState from 'apps/workflows/javascript/components/LoadingState'
import React, { useState, useRef, useEffect } from 'react'

import ReactFlow, {
  Controls,
  Edge,
  Node,
  Background,
  ConnectionLineType,
} from 'react-flow-renderer'
import { listWorkflows } from '../api'

import 'apps/workflows/javascript/styles/_dnd-flow.scss'
import LayoutButton from './LayoutButton'
import defaultNodeTypes from './Nodes'
import ZeroState from './ZeroState'
import useRunProgress from '../hooks/useRunProgress'
import { ScheduleContext } from '../context'

const GRID_GAP = 20

enum LoadingStates {
  loading,
  loaded,
  failed,
}

interface Props {
  projectId: number
  celeryProgressUrl: string
  runTaskUrl?: string
}

const ScheduleFlow: React.FC<Props> = ({ projectId, runTaskUrl, celeryProgressUrl }) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)

  const [elements, setElements] = useState<(Edge | Node)[]>([])
  const [initialLoad, setInitialLoad] = useState(LoadingStates.loading)

  const { runInfo } = useRunProgress(runTaskUrl, celeryProgressUrl)

  useEffect(() => {
    const syncElements = async () => {
      try {
        const [nodes, edges] = await listWorkflows(projectId)
        setElements([...nodes, ...edges])
        setInitialLoad(LoadingStates.loaded)
      } catch {
        setInitialLoad(LoadingStates.failed)
      }
    }

    syncElements()
  }, [])

  return (
    <ScheduleContext.Provider
      value={{
        runInfo,
      }}
    >
      <div className='reactflow-wrapper' ref={reactFlowWrapper}>
        <ReactFlow
          nodeTypes={defaultNodeTypes}
          elements={elements}
          connectionLineType={ConnectionLineType.SmoothStep}
          snapToGrid={true}
          snapGrid={[GRID_GAP, GRID_GAP]}
          maxZoom={2}
          minZoom={0.05}
        >
          <Controls>
            <LayoutButton elements={elements} setElements={setElements} />
          </Controls>
          <Background gap={GRID_GAP} />
          {initialLoad === LoadingStates.loading && <LoadingState />}
          {initialLoad === LoadingStates.failed && (
            <ErrorState error='Failed loading your nodes!' />
          )}
          {initialLoad === LoadingStates.loaded && elements.length === 0 && <ZeroState />}
        </ReactFlow>
      </div>
    </ScheduleContext.Provider>
  )
}

export default ScheduleFlow
