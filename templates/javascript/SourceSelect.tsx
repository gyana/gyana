import React, { Fragment, useEffect, useRef, useState } from 'react'
import { Listbox, Transition } from '@headlessui/react'
import ReactDOM from 'react-dom'

const SourceSelect_: React.FC<{ options; selected: number; name: string }> = ({
  options,
  selected,
  name,
}) => {
  const [option, setOption] = useState(
    () => options.filter((o) => o.id === selected)[0] || { id: '', label: '-----------' }
  )

  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (inputRef.current && option.id != selected) {
      // Manually fire the input change event for live update form
      // https://stackoverflow.com/a/36648958/15425660
      inputRef.current.dispatchEvent(new Event('change', { bubbles: true }))
    }
  }, [option.id])

  return (
    <Listbox value={option} onChange={setOption}>
      <Listbox.Button className='relative w-full py-2 pl-3 pr-10 text-left text-lg bg-white rounded-lg border border-gray focus:outline-none'>
        <span className='block truncate'>{option.label}</span>
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
        <Listbox.Options className='absolute text-lg w-full py-1 mt-1 overflow-auto bg-white rounded-md max-h-60 focus:outline-none border border-gray'>
          {options.map((o) => (
            <Listbox.Option
              key={o.id}
              value={o}
              className={({ active }) =>
                `${active ? 'text-black bg-gray-20' : 'text-black-50'}
                cursor-default select-none relative py-2 pl-4 pr-4 flex flex-row items-center`
              }
            >
              {({ selected, active }) => (
                <>
                  <i
                    className={`${o.type === 'integration' ? 'far fa-link' : 'far fa-stream'} mr-4`}
                  />
                  <span className={`${selected ? 'font-medium' : 'font-normal'} block truncate`}>
                    {o.label}
                  </span>
                  {selected ? (
                    <span
                      className={`${active ? 'text-black-50' : 'text-black-20'}
                            absolute inset-y-0 right-0 flex items-center pr-3`}
                    >
                      <i className='fa fa-check w-5 h-5' />
                    </span>
                  ) : null}
                </>
              )}
            </Listbox.Option>
          ))}
        </Listbox.Options>
      </Transition>
      <input ref={inputRef} type='hidden' name={name} id={`id_${name}`} value={option.id} />
    </Listbox>
  )
}

class SourceSelect extends HTMLElement {
  connectedCallback() {
    const mountPoint = document.createElement('div')
    // Because the Select dropdown will be absolute positioned we need to make the outer div relative
    mountPoint.setAttribute('class', 'relative')

    const options = JSON.parse(this.querySelector('#options').innerHTML)
    const selected = parseInt(this.attributes['selected'].value)
    const name = this.attributes['name'].value

    this.appendChild(mountPoint)
    ReactDOM.render(<SourceSelect_ options={options} selected={selected} name={name} />, mountPoint)
  }
}

export default SourceSelect
