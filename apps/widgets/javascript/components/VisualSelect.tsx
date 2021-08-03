import ReactDOM from 'react-dom'
import React, { useState } from 'react'
import { Listbox } from '@headlessui/react'
import {
  SelectButton,
  SelectOption,
  SelectTransition,
} from 'apps/utils/javascript/components/SelectComponents'
import useLiveUpdate from 'apps/utils/javascript/components/useLiveUpdate'

const VisualSelect_: React.FC<{
  selected: string
  options: { id: string; name: string; icon: string }[]
}> = ({ selected, options }) => {
  const [kind, setKind] = useState(options.filter((k) => k.id === selected)[0])

  const inputRef = useLiveUpdate(kind.id, selected)

  return (
    <Listbox value={kind} onChange={setKind}>
      <SelectButton>{kind.name}</SelectButton>
      <SelectTransition>
        <Listbox.Options className='absolute z-10 text-lg w-full py-1 mt-1 overflow-auto bg-white rounded-md max-h-60 focus:outline-none border border-gray'>
          {options.map((k) => (
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
    const options = JSON.parse(this.querySelector('#options')?.innerHTML || '[]')

    this.appendChild(mountPoint)
    ReactDOM.render(<VisualSelect_ selected={selected} options={options} />, mountPoint)
  }
}

export default VisualSelect
