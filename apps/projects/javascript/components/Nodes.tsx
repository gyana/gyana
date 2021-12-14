import Tippy from '@tippyjs/react'
import { EditButton, ScheduleButton } from './NodeButtons'
import React, { useContext, useEffect, useState } from 'react'
import { Handle, NodeProps, Position } from 'react-flow-renderer'
import { getIntegration, getWorkflow, updateConnector, updateSheet, updateWorkflow } from '../api'
import { IAutomateContext, AutomateContext } from '../context'

type ScheduleStatus = 'paused' | 'incomplete' | 'broken' | 'active'
type RunStatus = 'pending' | 'running' | 'done'

const SCHEDULE_STATUS_TO_MESSAGE: { [key in ScheduleStatus]: string } = {
  incomplete: 'Incomplete',
  paused: 'Paused',
  broken: 'Broken',
  active: 'Active',
}

const SCHEDULE_STATUS_TO_ICON: { [key in ScheduleStatus]: string } = {
  incomplete: 'fa-construction text-black-20',
  paused: 'fa-pause-circle text-black-20',
  broken: 'fa-times-circle text-red',
  active: 'fa-check-circle text-green',
}

interface StatusProps {
  scheduleStatus: ScheduleStatus
  runStatus: RunStatus
}

export const StatusIcon: React.FC<StatusProps> = ({ scheduleStatus, runStatus }) => {
  return (
    <Tippy content={SCHEDULE_STATUS_TO_MESSAGE[scheduleStatus]}>
      <div className='flex items-center justify-around absolute -top-2 -right-2 rounded-full w-6 h-6'>
        {runStatus === 'done' || scheduleStatus === 'paused' ? (
          <i className={`fa fa-2x fa-fw ${SCHEDULE_STATUS_TO_ICON[scheduleStatus]}`}></i>
        ) : (
          <div className='relative'>
            <i
              style={{ color: '#cbccd6' }}
              className={`fa fa-2x fa-fw absolute ${SCHEDULE_STATUS_TO_ICON[scheduleStatus]}`}
            ></i>
            <i
              className={`fad fa-fw fa-2x ${
                runStatus === 'running' ? 'fa-play-circle' : 'fa-spinner-third fa-spin'
              }`}
            ></i>
          </div>
        )}
      </div>
    </Tippy>
  )
}

const IntegrationNode: React.FC<NodeProps> = ({ id, data: initialData }) => {
  const [data, setData] = useState(initialData)
  const { runInfo } = useContext(AutomateContext) as IAutomateContext

  const sourceObj = data[data.kind]

  const initialRunStatus = sourceObj.run_status
  const runStatus = (runInfo?.run || runInfo[id] || initialRunStatus) as RunStatus

  useEffect(() => {
    const update = async () => {
      if (runStatus !== initialRunStatus && runStatus === 'done') {
        setData(await getIntegration(data.id))
      }
    }
    update()
  }, [runStatus])

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
      {data.kind !== 'upload' && (
        <StatusIcon scheduleStatus={sourceObj.schedule_status} runStatus={runStatus} />
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

  const { runInfo } = useContext(AutomateContext) as IAutomateContext
  const initialRunStatus = data.run_status
  const runStatus = (runInfo?.run || runInfo[id] || initialRunStatus) as RunStatus

  useEffect(() => {
    const update = async () => {
      if (runStatus !== initialRunStatus && runStatus === 'done') {
        setData(await getWorkflow(data.id))
      }
    }
    update()
  }, [runStatus])

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
      <StatusIcon scheduleStatus={data.schedule_status} runStatus={runStatus} />
      <Handle type='target' position={Position.Left} isConnectable={false} />
      <i
        className={`fas fa-fw fa-sitemap ${data.is_scheduled ? 'text-blue' : 'text-black-50'}`}
      ></i>
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
