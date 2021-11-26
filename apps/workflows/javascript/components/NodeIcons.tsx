import React from 'react'

interface Props {
  text: string
}

export const ErrorIcon: React.FC<Props> = ({ text }) => (
  <div
    title={text}
    className='flex items-center justify-around absolute -top-2 -right-2 bg-red-10 rounded-full w-6 h-6 text-red'
  >
    <i className='fad fa-bug '></i>
  </div>
)

export const WarningIcon: React.FC<Props> = ({ text }) => (
  <div
    className='flex items-center justify-around absolute -top-2 -left-2 rounded-full w-6 h-6 text-orange cursor-pointer'
    title={text}
  >
    <i className='fas fa-exclamation-triangle bg-white'></i>
  </div>
)
