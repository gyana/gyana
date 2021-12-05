import Tippy from '@tippyjs/react'
import NodeButtons from './NodeButtons'
import React from 'react'
import { Handle, NodeProps, Position } from 'react-flow-renderer'

export const ScheduledIcon: React.FC = ({ isScheduled }) => {
  const tooltip =
    isScheduled === true ? 'Scheduled' : isScheduled === false ? 'Paused' : 'Cannot be scheduled'

  return (
    <Tippy content={tooltip}>
      <div className='flex items-center justify-around absolute -top-2 -left-2 rounded-full w-6 h-6'>
        {isScheduled === true && <i className='fa fa-play-circle fa-2x text-green'></i>}
        {isScheduled === false && <i className='fa fa-pause-circle fa-2x text-black-20'></i>}
        {isScheduled === undefined && <i className='fa fa-ban fa-2x text-black-20'></i>}
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
      <ScheduledIcon isScheduled={sourceObj.is_scheduled} />
      <i className='fas fa-fw fa-database'></i>
      <Handle type='source' position={Position.Right} isConnectable={false} />
    </>
  )
}

const WorkflowNode: React.FC<NodeProps> = ({ id, data }) => (
  <>
    <p className='absolute -top-12'> {data.name}</p>
    <NodeButtons id={id} absoluteUrl={data.absolute_url} />
    <ScheduledIcon isScheduled={data.is_scheduled} />
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
