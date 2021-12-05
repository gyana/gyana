import React from 'react'
import { updateSchedulable } from '../api'

export const EditButton = ({ absoluteUrl }) => {
  return (
    <a className='text-black-50 hover:text-blue mt-3' href={absoluteUrl} title='Edit'>
      <i className='fas fa-fw fa-lg fa-edit'></i>
    </a>
  )
}

export const ScheduleButton = ({ id, model, isScheduled, fetchLatest }) => {
  return (
    <button
      onClick={async () => {
        await updateSchedulable(id, model, !isScheduled)
        fetchLatest()
      }}
      title={isScheduled ? 'Pause' : 'Play'}
    >
      <i className={`fas fa-fw fa-lg ${isScheduled ? 'fa-pause-circle' : 'fa-play-circle'}`} />
    </button>
  )
}
