import ReactDOM from 'react-dom'
import React, { useState } from 'react'
import { Listbox } from '@headlessui/react'
import { SelectButton, SelectOption, SelectOptions, SelectTransition } from './SelectComponents'

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
      <SelectButton>{kind.name}</SelectButton>
      <SelectTransition>
        <SelectOptions>
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
        </SelectOptions>
      </SelectTransition>
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
