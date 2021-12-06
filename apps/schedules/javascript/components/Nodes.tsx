import Tippy from '@tippyjs/react'
import { EditButton, ScheduleButton } from './NodeButtons'
import React, { useState } from 'react'
import { Handle, NodeProps, Position } from 'react-flow-renderer'
import { getIntegration, getWorkflow, updateConnector, updateSheet, updateWorkflow } from '../api'

interface StatusProps {
  succeeded: boolean
  isScheduled: boolean
}

export const StatusIcon: React.FC<StatusProps> = ({ succeeded, isScheduled }) => {
  return (
    <Tippy content={!isScheduled ? 'Paused' : succeeded ? 'Active' : 'Broken'}>
      <div className='flex items-center justify-around absolute -top-2 -right-2 rounded-full w-6 h-6'>
        {!isScheduled ? (
          <i className='fa fa-pause-circle fa-2x text-black-20'></i>
        ) : succeeded ? (
          <i className='fa fa-check-circle fa-2x text-green'></i>
        ) : (
          <i className='fa fa-times-circle fa-2x text-red'></i>
        )}
      </div>
    </Tippy>
  )
}

const IntegrationNode: React.FC<NodeProps> = ({ id, data: initialData }) => {
  const [data, setData] = useState(initialData)

  const sourceObj = data[data.kind]

  return (
    <>
      <p className='absolute -top-12'> {data.name}</p>
      <div className='react-flow__buttons'>
        {data.kind !== 'upload' && (
          <ScheduleButton
            isScheduled={sourceObj.is_scheduled}
            onClick={async () => {
              if (data.kind == 'connector')
                await updateConnector(sourceObj.id, { is_scheduled: !sourceObj.is_scheduled })
              else if (data.kind == 'sheet')
                await updateSheet(sourceObj.id, { is_scheduled: !sourceObj.is_scheduled })
              setData(await getIntegration(data.id))
            }}
          />
        )}
        <EditButton absoluteUrl={data.absolute_url} />
      </div>
      {sourceObj.is_scheduled !== undefined && (
        <StatusIcon succeeded={sourceObj.succeeded} isScheduled={sourceObj.is_scheduled} />
      )}
      <img
        className={`h-24 w-24 ${!sourceObj.is_scheduled ? 'filter grayscale' : ''}`}
        src={`/static/${data.icon}`}
      />
      <Handle type='source' position={Position.Right} isConnectable={false} />
    </>
  )
}

const WorkflowNode: React.FC<NodeProps> = ({ id, data: initialData }) => {
  const [data, setData] = useState(initialData)

  return (
    <>
      <p className='absolute -top-12'> {data.name}</p>
      <div className='react-flow__buttons'>
        <ScheduleButton
          isScheduled={data.is_scheduled}
          onClick={async () => {
            setData(await updateWorkflow(data.id, { is_scheduled: !data.is_scheduled }))
          }}
        />
        <EditButton absoluteUrl={data.absolute_url} />
      </div>
      <StatusIcon succeeded={data.succeeded} isScheduled={data.is_scheduled} />
      <Handle type='target' position={Position.Left} isConnectable={false} />
      <i
        className={`fas fa-fw fa-sitemap ${data.is_scheduled ? 'text-blue' : 'text-black-50'}`}
      ></i>
      <Handle type='source' position={Position.Right} isConnectable={false} />
    </>
  )
}

const DashboardNode: React.FC<NodeProps> = ({ id, data }) => {
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
