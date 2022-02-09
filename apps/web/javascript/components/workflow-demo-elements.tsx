import React from 'react'

export const getInputNodeLabel = (idx) => {
  const integration = window.__demo_store__.integrations[idx]

  return (
    <div className='relative w-full h-full'>
      <img
        src={`/static/images/integrations/fivetran/${integration.icon_path}`}
        className='h-full w-full pointer-events-none p-6'
      />
      <div className='absolute -bottom-12 left-0 right-0 text-2xl font-semibold text-gray-600'>
        {integration.name}
      </div>
    </div>
  )
}

export default [
  {
    id: '1',
    type: 'input',
    data: {
      label: getInputNodeLabel(0),
    },
    position: { x: 0, y: 200 },
  },
  {
    id: '2',
    type: 'input',
    data: {
      label: getInputNodeLabel(1),
    },
    position: { x: 0, y: 400 },
  },
  {
    id: '3',
    data: {
      label: (
        <div className='relative w-full h-full flex items-center justify-center'>
          <div>
            <i className='fa fa-link fa-8x'></i>
          </div>
          <div className='absolute -bottom-12 left-0 right-0 text-2xl font-semibold text-gray-600'>
            Combine rows
          </div>
        </div>
      ),
    },
    position: { x: 100, y: 300 },
  },
  {
    id: '4',
    type: 'placeholder',
    data: {
      label: (
        <div className='w-full h-full flex items-center justify-center'>
          <i className='fa fa-question fa-8x text-gray'></i>
        </div>
      ),
    },
    position: { x: 200, y: 300 },
  },
  {
    id: '5',
    type: 'output',
    data: {
      label: (
        <div className='relative w-full h-full flex items-center justify-center'>
          <div>
            <i className='fa fa-save fa-8x'></i>
          </div>
          <div className='absolute -bottom-12 left-0 right-0 text-2xl font-semibold text-gray-600'>
            Save table
          </div>
        </div>
      ),
    },
    position: { x: 300, y: 300 },
  },
  { id: 'e1-3', source: '1', target: '3', style: { strokeWidth: 10, stroke: '#e6e6e6' } },
  { id: 'e2-3', source: '2', target: '3', style: { strokeWidth: 10, stroke: '#e6e6e6' } },
  { id: 'e3-4', source: '3', target: '4', style: { strokeWidth: 10, stroke: 'none' } },
  { id: 'e4-5', source: '4', target: '5', style: { strokeWidth: 10, stroke: 'none' } },
]
