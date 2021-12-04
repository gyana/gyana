import ErrorState from 'apps/workflows/javascript/components/ErrorState'
import LoadingState from 'apps/workflows/javascript/components/LoadingState'
import ZeroState from 'apps/workflows/javascript/components/ZeroState'
import React, { useState, useRef, useEffect } from 'react'

import ReactFlow, {
  Controls,
  Edge,
  Node,
  useZoomPanHelper,
  Background,
  ConnectionLineType,
  useStoreState,
} from 'react-flow-renderer'
import { listWorkflows } from '../api'

import 'apps/workflows/javascript/styles/_dnd-flow.scss'
import { getLayoutedElements } from 'apps/workflows/javascript/layout'

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
  const { fitView } = useZoomPanHelper()

  const [elements, setElements] = useState<(Edge | Node)[]>([])
  const [initialLoad, setInitialLoad] = useState(LoadingStates.loading)
  const [shouldLayout, setShouldLayout] = useState(true)

  useEffect(() => {
    const syncElements = async () => {
      // try {
      const [nodes, edges] = await listWorkflows(projectId)
      setElements([...nodes, ...edges])
      setInitialLoad(LoadingStates.loaded)
      // } catch {
      //   setInitialLoad(LoadingStates.failed)
      // }
    }

    syncElements()
  }, [])

  const nodes = useStoreState((state) => state.nodes)

  useEffect(() => {
    if (shouldLayout && nodes.length > 0 && nodes.every((el) => el.__rf.width && el.__rf.height)) {
      setElements(getLayoutedElements(elements, nodes))
      fitView()
      setShouldLayout(false)
    }
  }, [shouldLayout, nodes])

  return (
    <div className='reactflow-wrapper' ref={reactFlowWrapper}>
      <ReactFlow
        // nodeTypes={defaultNodeTypes}
        elements={elements}
        connectionLineType={ConnectionLineType.SmoothStep}
        snapToGrid={true}
        snapGrid={[GRID_GAP, GRID_GAP]}
        maxZoom={2}
        minZoom={0.05}
      >
        <Controls />
        <Background gap={GRID_GAP} />
        {initialLoad === LoadingStates.loading && <LoadingState />}
        {initialLoad === LoadingStates.failed && <ErrorState error='Failed loading your nodes!' />}
        {/* TODO: Add a zero state */}
        {/* {initialLoad === LoadingStates.loaded && elements.length === 0 && <ZeroState />} */}
      </ReactFlow>
    </div>
  )
}

export default ScheduleFlow
