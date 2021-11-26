import React from 'react'

interface Props {
  text: string
}

export const ErrorIcon: React.FC<Props> = ({ text }) => (
  <div
    className='flex items-center justify-around absolute -top-2 -right-2 bg-red-10 rounded-full w-6 h-6 text-red'
    data-controller='tooltip'
  >
    <i className='fa fa-bug fa-2x'></i>
    <template data-tooltip-target='body'>There was an error running this node</template>
  </div>
)

export const WarningIcon: React.FC<Props> = ({ text }) => (
  <div
    className='flex items-center justify-around absolute -top-2 -left-2 rounded-full w-6 h-6 text-orange cursor-pointer'
    data-controller='tooltip'
  >
    <i className='fa fa-exclamation-triangle fa-2x'></i>
    <template data-tooltip-target='body'>{text}</template>
  </div>
)
