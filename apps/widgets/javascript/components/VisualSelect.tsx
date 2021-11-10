import ReactDOM from 'react-dom'
import React, { useEffect, useState } from 'react'
import { Listbox } from '@headlessui/react'
import {
  SelectButton,
  SelectOption,
  SelectTransition,
} from 'apps/base/javascript/components/SelectComponents'
import useLiveUpdate from 'apps/base/javascript/components/useLiveUpdate'
import { GyanaEvents } from 'apps/base/javascript/events'

const getFormParent = (el) => {
  if (el.tagName == 'FORM') {
    return el
  }
  return getFormParent(el.parentNode)
}

const VisualSelect_: React.FC<{
  selected: string
  options: { id: string; name: string; icon: string; maxMetrics: number }[]
}> = ({ selected, options }) => {
  const [kind, setKind] = useState(options.filter((k) => k.id === selected)[0])
  const [totalMetrics, setTotalMetrics] = useState(0)
  const inputRef = useLiveUpdate(kind.id, selected)

  const updateTotalMetrics = () => {
    const formParent = getFormParent(inputRef.current)
    const input = formParent.querySelector('[name="aggregations-TOTAL_FORMS"]')
    if (input) {
      const totalRows = parseInt(input.value)
      const deletedRows = formParent.querySelectorAll('input[name$=DELETE][value=on]').length
      setTotalMetrics(totalRows - deletedRows)
    }
  }

  useEffect(() => {
    if (inputRef.current) {
      updateTotalMetrics()
      window.addEventListener(GyanaEvents.UPDATE_FORM_COUNT, updateTotalMetrics)
      return () => window.removeEventListener(GyanaEvents.UPDATE_FORM_COUNT, updateTotalMetrics)
    }
  }, [])

  return (
    <Listbox value={kind} onChange={setKind}>
      <SelectButton>{kind.name}</SelectButton>
      <SelectTransition>
        <Listbox.Options className='absolute z-10 text-lg w-full py-1 mt-1 overflow-auto bg-white rounded-md max-h-60 focus:outline-none border border-gray'>
          {options.map((k) => {
            const disabled = k.maxMetrics != -1 && k.maxMetrics < totalMetrics
            return (
              <SelectOption key={k.id} value={k} disabled={disabled}>
                {({ selected, active }) => (
                  <div
                    className='flex flex-row items-center'
                    data-controller={disabled && 'tooltip'}
                  >
                    <i
                      className={`fad ${k.icon} ${disabled ? 'text-black-20' : 'text-blue'} mr-4`}
                    />
                    <span className={`${selected ? 'font-medium' : 'font-normal'} block truncate`}>
                      {k.name}
                    </span>
                    {disabled && (
                      <span data-tooltip-target='body'>
                        The current chart has too many metrics to change to a {k.name} chart. Reduce
                        to {k.maxMetrics} metric to change.
                      </span>
                    )}
                  </div>
                )}
              </SelectOption>
            )
          })}
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

  disconnectedCallback() {
    ReactDOM.unmountComponentAtNode(this)
  }
}

export default VisualSelect
