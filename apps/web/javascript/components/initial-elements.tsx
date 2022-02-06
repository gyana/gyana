import React from 'react'

export default [
  {
    id: '1',
    type: 'input',
    data: {
      label: (
        <div className='relative'>
          <img
            className='pointer-events-none'
            src='/static/images/integrations/fivetran/google_ads_account.png'
          />
          <div className='absolute -bottom-12 left-0 right-0 text-2xl font-semibold text-gray-600'>
            Google Ads
          </div>
        </div>
      ),
    },
    position: { x: 0, y: 200 },
  },
  {
    id: '2',
    type: 'input',
    data: {
      label: (
        <div className='relative'>
          <img
            src='/static/images/integrations/fivetran/facebook_ads.svg'
            className='h-full w-full pointer-events-none'
          />
          <div className='absolute -bottom-12 left-0 right-0 text-2xl font-semibold text-gray-600'>
            Facebook Ads
          </div>
        </div>
      ),
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
      label: '',
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
  { id: 'e1-3', source: '1', target: '3', animated: true },
  { id: 'e2-3', source: '2', target: '3', animated: true },
  { id: 'e3-4', source: '3', target: '4', animated: true },
  { id: 'e4-5', source: '4', target: '5', animated: true },
]
