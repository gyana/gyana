import { Listbox, Transition } from '@headlessui/react'
import React, { Fragment } from 'react'

export const SelectButton = ({ children }) => (
  <Listbox.Button className='relative w-full text-2xl py-4 pl-8 pr-10 text-left bg-white rounded-lg border border-gray focus:outline-none'>
    <span className='block truncate'>{children}</span>
    <span className='absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none'>
      <i className='text-gray fa fa-chevron-down' />
    </span>
  </Listbox.Button>
)

export const SelectTransition = ({ children }) => (
  <Transition
    as={Fragment}
    leave='transition ease-in duration-100'
    leaveFrom='opacity-100'
    leaveTo='opacity-0'
  >
    {children}
  </Transition>
)

export const SelectOption = ({ children, value, disabled = false }) => (
  <Listbox.Option
    value={value}
    disabled={disabled}
    className={({ active }) =>
      `${disabled ? 'text-black-20' : active ? 'text-black bg-gray-20' : 'text-black-50'}
                cursor-pointer select-none relative py-2 pl-4 pr-4 flex flex-row items-center`
    }
  >
    {({ selected, active }) => children(selected, active)}
  </Listbox.Option>
)
