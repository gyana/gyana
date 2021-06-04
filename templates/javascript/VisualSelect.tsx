import ReactDOM from 'react-dom'
import React, { useState } from 'react'
import { Listbox } from '@headlessui/react'
import { SelectButton, SelectOption, SelectTransition } from './SelectComponents'
import useLiveUpdate from './useLiveUpdate'

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

  const inputRef = useLiveUpdate(kind.id, selected)

  return (
    <Listbox value={kind} onChange={setKind}>
      <SelectButton>{kind.name}</SelectButton>
      <SelectTransition>
        <Listbox.Options className='absolute z-10 text-lg w-full py-1 mt-1 overflow-auto bg-white rounded-md max-h-60 focus:outline-none border border-gray'>
          {VisualKinds.map((k) => (
            <SelectOption key={k.id} value={k}>
              {({ selected, active }) => (
                <div className='flex flex-row items-center'>
                  <i className={`fad ${k.icon} text-blue mr-4`} />
                  <span className={`${selected ? 'font-medium' : 'font-normal'} block truncate`}>
                    {k.name}
                  </span>
                </div>
              )}
            </SelectOption>
          ))}
        </Listbox.Options>
      </SelectTransition>
      <input ref={inputRef} type='hidden' name='kind' id='id_kind' value={kind.id} />
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
