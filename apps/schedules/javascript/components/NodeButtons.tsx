import React from 'react'
import { updateSchedulable } from '../api'

export const EditButton = ({ absoluteUrl }) => {
  return (
    <a className='text-black-50 mt-3' href={absoluteUrl} title='Edit'>
      <i className='fas fa-fw fa-lg fa-edit'></i>
    </a>
  )
}

export const ScheduleButton = ({ id, model, isScheduled }) => {
  return (
    <button
      onClick={() => updateSchedulable(id, model, !isScheduled)}
      title={isScheduled ? 'Pause' : 'Play'}
    >
      <i className={`fas fa-fw fa-lg ${isScheduled ? 'fa-pause-circle' : 'fa-play-circle'}`} />
    </button>
  )
}
