import Tippy from '@tippyjs/react'
import NodeButtons from './NodeButtons'
import React from 'react'
import { Handle, NodeProps, Position } from 'react-flow-renderer'

interface Props {
  isScheduled: boolean
}

export const ScheduledIcon: React.FC<Props> = ({ isScheduled }) => {
  return (
    <Tippy content={isScheduled ? 'Scheduled' : 'Paused'}>
      <div className='flex items-center justify-around absolute -top-2 -left-2 rounded-full w-6 h-6'>
        {isScheduled ? (
          <i className='fa fa-play-circle fa-2x text-green'></i>
        ) : (
          <i className='fa fa-pause-circle fa-2x text-black-20'></i>
        )}
      </div>
    </Tippy>
  )
}

interface StatusProps {
  succeeded: boolean
}

export const StatusIcon: React.FC<StatusProps> = ({ succeeded }) => {
  return (
    <Tippy content={succeeded ? 'Most recent run succeeded' : 'Most recent run failed'}>
      <div className='flex items-center justify-around absolute -top-2 -right-2 rounded-full w-6 h-6'>
        {succeeded ? (
          <i className='fa fa-check-circle fa-2x text-green'></i>
        ) : (
          <i className='fa fa-times-circle fa-2x text-red'></i>
        )}
      </div>
    </Tippy>
  )
}

const IntegrationNode: React.FC<NodeProps> = ({ id, data }) => {
  const sourceObj = data[data.kind]

  return (
    <>
      <p className='absolute -top-12'> {data.name}</p>
      <NodeButtons id={id} absoluteUrl={data.absolute_url} />
      {sourceObj.is_scheduled !== undefined && (
        <ScheduledIcon isScheduled={sourceObj.is_scheduled} />
      )}
      <StatusIcon succeeded={data.succeeded} />
      <img className='h-24 w-24' src={`/static/${data.icon}`} title='{{ object.name }}' />
      <Handle type='source' position={Position.Right} isConnectable={false} />
    </>
  )
}

const WorkflowNode: React.FC<NodeProps> = ({ id, data }) => (
  <>
    <p className='absolute -top-12'> {data.name}</p>
    <NodeButtons id={id} absoluteUrl={data.absolute_url} />
    <ScheduledIcon isScheduled={data.is_scheduled} />
    <StatusIcon succeeded={data.succeeded} />
    <Handle type='target' position={Position.Left} isConnectable={false} />
    <i className='fas fa-fw fa-sitemap'></i>
    <Handle type='source' position={Position.Right} isConnectable={false} />
  </>
)

const DashboardNode: React.FC<NodeProps> = ({ id, data }) => (
  <>
    <p className='absolute -top-12'> {data.name}</p>
    <NodeButtons id={id} absoluteUrl={data.absolute_url} />
    <Handle type='target' position={Position.Left} isConnectable={false} />
    <i className='fas fa-fw fa-chart-pie'></i>
  </>
)

const defaultNodeTypes = {
  integration: IntegrationNode,
  workflow: WorkflowNode,
  dashboard: DashboardNode,
}

export default defaultNodeTypes
