import React, { useState } from 'react'
import { Listbox } from '@headlessui/react'
import ReactDOM from 'react-dom'

const SourceSelect_: React.FC<{ options; selected: number }> = ({ options, selected }) => {
  const [option, setOption] = useState(() => options.filter((o) => o.id === selected)[0])

  return (
    <Listbox value={option} onChange={setOption}>
      <Listbox.Button>{option.label}</Listbox.Button>
      <Listbox.Options>
        {options.map((o) => (
          <Listbox.Option key={o.id} value={o}>
            {o.label}
          </Listbox.Option>
        ))}
      </Listbox.Options>
      <input type='hidden' name='input_table' value={option.id} />
    </Listbox>
  )
}

class SourceSelect extends HTMLElement {
  connectedCallback() {
    const mountPoint = document.createElement('div')

    const options = JSON.parse(this.attributes['options'].value)
    const selected = parseInt(this.attributes['selected'].value)

    this.appendChild(mountPoint)
    ReactDOM.render(<SourceSelect_ options={options} selected={selected} />, mountPoint)
  }
}

export default SourceSelect
