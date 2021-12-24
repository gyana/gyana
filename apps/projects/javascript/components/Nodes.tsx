import Tippy from '@tippyjs/react'
import { EditButton } from './NodeButtons'
import React, { useContext, useEffect, useState } from 'react'
import { Handle, NodeProps, Position } from 'react-flow-renderer'
import { getIntegration, getWorkflow } from '../api'
import { IAutomateContext, AutomateContext } from '../context'

type State = 'pending' | 'running' | 'failed' | 'success'

const STATE_TO_MESSAGE: { [key in State]: string } = {
  pending: 'Pending',
  running: 'Running',
  failed: 'Failed',
  success: 'Success',
}

const STATE_TO_ICON: { [key in State]: string } = {
  pending: 'fa-clock',
  running: 'fa-spinner-third fa-spin',
  failed: 'fa-times-circle text-red',
  success: 'fa-check-circle text-green',
}

interface StateProps {
  state: State
}

export const StatusIcon: React.FC<StateProps> = ({ state }) => {
  return (
    <Tippy content={STATE_TO_MESSAGE[state]}>
      <div
        data-cy-status={state}
        className='flex items-center justify-around absolute -top-2 -right-2 rounded-full w-6 h-6'
      >
        <i className={`fad fa-2x fa-fw ${STATE_TO_ICON[state]}`}></i>
      </div>
    </Tippy>
  )
}

const IntegrationNode: React.FC<NodeProps> = ({ id, data: initialData }) => {
  const [data, setData] = useState(initialData)
  const { runInfo } = useContext(AutomateContext) as IAutomateContext

  // not defined for connectors, for now
  const state = data.latest_run?.state
  const progressRunState = (runInfo.project || runInfo[id] || state) as State

  useEffect(() => {
    const update = async () => {
      if (progressRunState !== state) {
        setData(await getIntegration(data.id))
      }
    }
    update()
  }, [progressRunState])

  return (
    <>
      <p className='absolute -top-12'> {data.name}</p>
      <div className='react-flow__buttons'>
        <EditButton absoluteUrl={data.absolute_url} />
      </div>
      {state && <StatusIcon state={state} />}
      <img className='h-24 w-24' src={`/static/${data.icon}`} />
      <Handle type='source' position={Position.Right} isConnectable={false} />
    </>
  )
}

const WorkflowNode: React.FC<NodeProps> = ({ id, data: initialData }) => {
  const [data, setData] = useState(initialData)

  const { runInfo } = useContext(AutomateContext) as IAutomateContext
  const state = data.latest_run?.state
  const progressState = (runInfo.project || runInfo[id] || state) as RunState

  useEffect(() => {
    const update = async () => {
      if (progressState !== state) {
        setData(await getWorkflow(data.id))
      }
    }
    update()
  }, [progressState])

  return (
    <>
      <p className='absolute -top-12'> {data.name}</p>
      <div className='react-flow__buttons'>
        <EditButton absoluteUrl={data.absolute_url} />
      </div>
      {state && <StatusIcon state={state} />}
      <Handle type='target' position={Position.Left} isConnectable={false} />
      <i className='fas fa-fw fa-sitemap'></i>
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
