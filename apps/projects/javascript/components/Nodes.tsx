import Tippy from '@tippyjs/react'
import { EditButton } from './NodeButtons'
import React, { useContext, useEffect, useState } from 'react'
import { Handle, NodeProps, Position } from 'react-flow-renderer'
import { getIntegration, getWorkflow } from '../api'
import { IAutomateContext, AutomateContext } from '../context'

type RunState = 'pending' | 'running' | 'failed' | 'success'

const STATE_TO_MESSAGE: { [key in RunState]: string } = {
  pending: 'Pending',
  running: 'Running',
  failed: 'Failed',
  success: 'Success',
}

const STATE_TO_ICON: { [key in RunState]: string } = {
  pending: 'fa-clock',
  running: 'fa-spinner-third fa-spin',
  failed: 'fa-times-circle text-red',
  success: 'fa-check-circle text-green',
}

interface StateProps {
  runState: RunState
}

export const StatusIcon: React.FC<StateProps> = ({ runState }) => {
  return (
    <Tippy content={STATE_TO_MESSAGE[runState]}>
      <div className='flex items-center justify-around absolute -top-2 -right-2 rounded-full w-6 h-6'>
        <i className={`fad fa-2x fa-fw ${STATE_TO_ICON[runState]}`}></i>
      </div>
    </Tippy>
  )
}

const IntegrationNode: React.FC<NodeProps> = ({ id, data: initialData }) => {
  const [data, setData] = useState(initialData)
  const { runInfo } = useContext(AutomateContext) as IAutomateContext

  // not defined for connectors, for now
  const initialRunState = data.latest_run?.state
  const runState = (runInfo?.project || runInfo[id] || initialRunState) as RunState

  useEffect(() => {
    const update = async () => {
      if (runState !== initialRunState) {
        setData(await getIntegration(data.id))
      }
    }
    update()
  }, [runState])

  return (
    <>
      <p className='absolute -top-12'> {data.name}</p>
      <div className='react-flow__buttons'>
        <EditButton absoluteUrl={data.absolute_url} />
      </div>
      {data.kind === 'sheet' && <StatusIcon runState={data.latest_run.state} />}
      <img className='h-24 w-24' src={`/static/${data.icon}`} />
      <Handle type='source' position={Position.Right} isConnectable={false} />
    </>
  )
}

const WorkflowNode: React.FC<NodeProps> = ({ id, data: initialData }) => {
  const [data, setData] = useState(initialData)

  const { runInfo } = useContext(AutomateContext) as IAutomateContext
  const initialRunState = data.latest_run.state
  const runState = (runInfo?.project || runInfo[id] || initialRunState) as RunState

  useEffect(() => {
    const update = async () => {
      if (runState !== initialRunState) {
        setData(await getWorkflow(data.id))
      }
    }
    update()
  }, [runState])

  return (
    <>
      <p className='absolute -top-12'> {data.name}</p>
      <div className='react-flow__buttons'>
        <EditButton absoluteUrl={data.absolute_url} />
      </div>
      <StatusIcon runState={data.latest_run.state} />
      <Handle type='target' position={Position.Left} isConnectable={false} />
      <i className='fas fa-fw fa-sitemap text-blue'></i>
      <Handle type='source' position={Position.Right} isConnectable={false} />
    </>
  )
}

const DashboardNode: React.FC<NodeProps> = ({ data }) => {
  return (
    <>
      <p className='absolute -top-12'> {data.name}</p>
      <div className='react-flow__buttons'>
        <EditButton absoluteUrl={data.absolute_url} />
      </div>
      <Handle type='target' position={Position.Left} isConnectable={false} />
      <i className='fas fa-fw fa-chart-pie'></i>
    </>
  )
}

const defaultNodeTypes = {
  integration: IntegrationNode,
  workflow: WorkflowNode,
  dashboard: DashboardNode,
}

export default defaultNodeTypes
