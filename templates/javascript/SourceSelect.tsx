import React, { Fragment, useState } from 'react'
import { Listbox, Transition } from '@headlessui/react'
import ReactDOM from 'react-dom'

const SourceSelect_: React.FC<{ options; selected: number }> = ({ options, selected }) => {
  const [option, setOption] = useState(() => options.filter((o) => o.id === selected)[0])

  return (
    <Listbox value={option} onChange={setOption}>
      <Listbox.Button className='relative w-full py-2 pl-3 pr-10 text-left bg-white rounded-lg border border-gray'>
        <span className='block truncate'>{option.label}</span>
        <span className='absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none'>
          <i className='w-5 h-5 text-gray fa fa-chevron-down' />
        </span>
      </Listbox.Button>
      <Transition
        as={Fragment}
        leave='transition ease-in duration-100'
        leaveFrom='opacity-100'
        leaveTo='opacity-0'
      >
        <Listbox.Options className='absolute w-full py-1 mt-1 overflow-auto text-base bg-white rounded-md max-h-60 focus:outline-none border border-gray'>
          {options.map((o) => (
            <Listbox.Option
              key={o.id}
              value={o}
              className={({ active }) =>
                `${active ? 'text-orange bg-orange-20' : 'text-black-50'}
                cursor-default select-none relative py-2 pl-8 pr-4 flex flex-row items-center`
              }
            >
              {({ selected, active }) => (
                <>
                  <i
                    className={`${o.type === 'integration' ? 'far fa-link' : 'far fa-stream'} mr-3`}
                  />
                  <span className={`${selected ? 'font-medium' : 'font-normal'} block truncate`}>
                    {o.label}
                  </span>
                  {selected ? (
                    <span
                      className={`${active ? 'text-orange' : 'text-orange-50'}
                            absolute inset-y-0 right-0 flex items-center pr-3`}
                    >
                      <i className='fad fa-check w-5 h-5' />
                    </span>
                  ) : null}
                </>
              )}
            </Listbox.Option>
          ))}
        </Listbox.Options>
      </Transition>
      <input type='hidden' name='input_table' value={option.id} />
    </Listbox>
  )
}

class SourceSelect extends HTMLElement {
  connectedCallback() {
    const mountPoint = document.createElement('div')
    // Because the Select dropdown will be absolute positioned we need to make the outer div relative
    mountPoint.setAttribute('class', 'relative')

    const options = JSON.parse(this.attributes['options'].value)
    const selected = parseInt(this.attributes['selected'].value)

    this.appendChild(mountPoint)
    ReactDOM.render(<SourceSelect_ options={options} selected={selected} />, mountPoint)
  }
}

export default SourceSelect
