import React from 'react'

interface Props {
  text: string
}

export const ErrorIcon: React.FC<Props> = ({ text }) => (
  <div className='flex items-center justify-around z-10 absolute -top-2 -right-2 bg-red-10 rounded-full w-6 h-6 text-red'>
    <i
      className='fa fa-bug fa-2x'
      x-tooltip='There was an error running this node'
    ></i>
  </div>
)

export const WarningIcon: React.FC<Props> = ({ text }) => (
  <div className='flex items-center justify-around z-10 absolute -top-2 -left-2 rounded-full w-6 h-6 text-orange'>
    <i className='fa fa-exclamation-triangle fa-2x' x-tooltip={text}></i>
  </div>
)
