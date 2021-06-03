import { Listbox } from '@headlessui/react'
import React from 'react'

const SelectButton = ({ children }) => (
  <Listbox.Button className='relative w-full text-2xl py-4 pl-8 pr-10 text-left bg-white rounded-lg border border-gray focus:outline-none'>
    <span className='block truncate'>{children}</span>
    <span className='absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none'>
      <i className='text-gray fa fa-chevron-down' />
    </span>
  </Listbox.Button>
)

export default SelectButton
