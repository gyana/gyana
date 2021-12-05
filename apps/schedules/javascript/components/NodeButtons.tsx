import React from 'react'
import { updateSchedulable } from '../api'

const EditButton = ({ absoluteUrl }) => {
  return (
    <a className='text-black-50 mt-3' href={absoluteUrl} title='Edit'>
      <i className='fas fa-fw fa-lg fa-edit'></i>
    </a>
  )
}

const ScheduleButton = ({ id, model, isScheduled }) => {
  return (
    <button
      onClick={() => updateSchedulable(id, model, !isScheduled)}
      title={isScheduled ? 'Pause' : 'Play'}
    >
      <i className={`fas fa-fw fa-lg ${isScheduled ? 'fa-pause-circle' : 'fa-play-circle'}`} />
    </button>
  )
}

const NodeButtons = ({ id, model, isScheduled, absoluteUrl, schedulable }) => {
  return (
    <div className='react-flow__buttons'>
      {schedulable && <ScheduleButton id={id} model={model} isScheduled={isScheduled} />}
      <EditButton absoluteUrl={absoluteUrl} />
    </div>
  )
}

export default NodeButtons
