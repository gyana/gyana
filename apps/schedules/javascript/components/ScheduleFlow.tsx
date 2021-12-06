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

const GRID_GAP = 20

enum LoadingStates {
  loading,
  loaded,
  failed,
}

interface Props {
  projectId: number
}

const ScheduleFlow: React.FC<Props> = ({ projectId }) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)

  const [elements, setElements] = useState<(Edge | Node)[]>([])
  const [initialLoad, setInitialLoad] = useState(LoadingStates.loading)

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
        {initialLoad === LoadingStates.failed && <ErrorState error='Failed loading your nodes!' />}
        {initialLoad === LoadingStates.loaded && elements.length === 0 && <ZeroState />}
      </ReactFlow>
    </div>
  )
}

export default ScheduleFlow
