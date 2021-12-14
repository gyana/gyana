import React from 'react'

export const EditButton = ({ absoluteUrl }) => {
  return (
    <a className='text-black-50 hover:text-blue mt-3' href={absoluteUrl} title='Edit'>
      <i className='fas fa-fw fa-lg fa-edit'></i>
    </a>
  )
}

export const ScheduleButton = ({ isScheduled, onClick }) => {
  return (
    <button onClick={onClick} title={isScheduled ? 'Pause' : 'Play'}>
      <i className={`fas fa-fw fa-lg ${isScheduled ? 'fa-pause-circle' : 'fa-play-circle'}`} />
    </button>
  )
}
