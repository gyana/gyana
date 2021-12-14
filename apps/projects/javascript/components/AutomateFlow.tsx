import ErrorState from 'apps/base/javascript/components/ErrorState'
import LoadingState from 'apps/base/javascript/components/LoadingState'
import React, { useState, useRef, useEffect } from 'react'
import ReactDOM from 'react-dom'
import ReactFlow, {
  Controls,
  Edge,
  Node,
  Background,
  ConnectionLineType,
} from 'react-flow-renderer'
import { listProjectAll } from '../api'

import 'apps/base/javascript/styles/_react-flow.scss'
import LayoutButton from './LayoutButton'
import defaultNodeTypes from './Nodes'
import ZeroState from './ZeroState'
import { AutomateContext } from '../context'
import RunButton from './RunButton'

const GRID_GAP = 20

enum LoadingStates {
  loading,
  loaded,
  failed,
}

interface Props {
  projectId: number
}

const AutomateFlow: React.FC<Props> = ({ projectId }) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)

  const [elements, setElements] = useState<(Edge | Node)[]>([])
  const [initialLoad, setInitialLoad] = useState(LoadingStates.loading)
  const [runInfo, setRunInfo] = useState({})

  useEffect(() => {
    const syncElements = async () => {
      try {
        const [nodes, edges] = await listProjectAll(projectId)
        setElements([...nodes, ...edges])
        setInitialLoad(LoadingStates.loaded)
      } catch {
        setInitialLoad(LoadingStates.failed)
      }
    }

    syncElements()
  }, [])

  return (
    <AutomateContext.Provider
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

      {ReactDOM.createPortal(
        <RunButton projectId={projectId} setRunInfo={setRunInfo} />,
        document.getElementById('run-button-portal') as HTMLDivElement
      )}
    </AutomateContext.Provider>
  )
}

export default AutomateFlow
