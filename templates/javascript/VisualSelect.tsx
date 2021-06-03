import ReactDOM from 'react-dom'
import React, { Fragment, useState } from 'react'
import { Listbox, Transition } from '@headlessui/react'

enum Kind {
  Table = 'table',
  Column = 'column2d',
  Line = 'line',
  Pie = 'pie2d',
}

const VisualKinds = [
  { id: Kind.Table, name: 'Table', icon: 'fa-table' },
  { id: Kind.Column, name: 'Bar', icon: 'fa-chart-bar' },
  { id: Kind.Pie, name: 'Pie', icon: 'fa-chart-pie' },
  { id: Kind.Line, name: 'Line', icon: 'fa-chart-line' },
]

const VisualSelect_: React.FC<{ selected: Kind }> = ({ selected }) => {
  const [kind, setKind] = useState(VisualKinds.filter((k) => k.id === selected)[0])

  return (
    <Listbox value={kind} onChange={setKind}>
      <Listbox.Button className='relative w-full text-2xl py-4 pl-8 pr-10 text-left bg-white rounded-lg border border-gray focus:outline-none'>
        <span className='block truncate'>{kind.name}</span>
        <span className='absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none'>
          <i className='text-gray fa fa-chevron-down' />
        </span>
      </Listbox.Button>
      <Transition
        as={Fragment}
        leave='transition ease-in duration-100'
        leaveFrom='opacity-100'
        leaveTo='opacity-0'
      >
        <Listbox.Options className='absolute text-lg w-full py-1 mt-1 overflow-auto bg-white rounded-md max-h-100 focus:outline-none border border-gray'>
          {VisualKinds.map((k) => (
            <Listbox.Option
              key={k.id}
              value={k}
              className={({ active, selected }) =>
                `${active ? 'text-black bg-gray-20' : 'text-black-50'}
                ${selected && 'bg-gray-50'}
         cursor-default select-none relative py-2 pl-4 pr-4 flex flex-row items-center`
              }
            >
              {({ selected, active }) => (
                <div className='flex flex-row items-center'>
                  <i className={`fad ${k.icon} text-blue mr-4`} />
                  <span className={`${selected ? 'font-medium' : 'font-normal'} block truncate`}>
                    {k.name}
                  </span>
                </div>
              )}
            </Listbox.Option>
          ))}
        </Listbox.Options>
      </Transition>
      <input type='hidden' name='kind' value={kind.id} />
    </Listbox>
  )
}
class VisualSelect extends HTMLElement {
  connectedCallback() {
    const mountPoint = document.createElement('div')

    // Because the Select dropdown will be absolute positioned we need to make the outer div relative
    mountPoint.setAttribute('class', 'relative')
    const selected = this.attributes['selected'].value

    this.appendChild(mountPoint)
    ReactDOM.render(<VisualSelect_ selected={selected} />, mountPoint)
  }
}

export default VisualSelect
