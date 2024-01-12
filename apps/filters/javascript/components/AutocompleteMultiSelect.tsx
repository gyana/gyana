import { Listbox, Transition } from '@headlessui/react'
import React, { Fragment, useEffect, useRef, useState } from 'react'
import ReactDOM from 'react-dom'
import {
  SelectButton,
  SelectOption,
} from 'apps/base/javascript/components/SelectComponents'

const findParentForm = (el) => {
  if (el.tagName == 'FORM') return el
  return findParentForm(el.parentNode)
}

const AutocompleteMultiSelect_: React.FC<{
  parentType: string
  parentId: string
  name: string
  selected
  column
}> = ({ parentType, parentId, name, selected, column }) => {
  const [options, setOptions] = useState<string[]>([])
  const [search, setSearch] = useState('')
  const [selectedOptions, setSelectedOptions] = useState<string[]>(selected)
  const searchRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  function isSelected(value) {
    return selectedOptions.find((el) => el === value) ? true : false
  }

  function handleSelect(value) {
    if (!isSelected(value)) {
      const selectedUpdated = [
        ...selectedOptions,
        options.find((el) => el === value) as string,
      ]
      setSelectedOptions(selectedUpdated)
      setSearch('')
    } else {
      handleDeselect(value)
    }
  }
  function handleDeselect(value) {
    const selectedUpdated = selectedOptions.filter((el) => el !== value)
    setSelectedOptions(selectedUpdated)
  }

  useEffect(() => {
    setLoading(true)
    let url = `/filters/autocomplete?q=${search}&column=${column}&parentType=${parentType}&parentId=${parentId}`
    const formData = new FormData(findParentForm(inputRef.current))
    const tableId = formData.get('table')
    if (tableId) {
      url = `${url}&tableId=${tableId}`
    }
    fetch(url)
      .then((res) => res.json())
      .then((r) => {
        setOptions(r)
        setLoading(false)
        searchRef.current?.focus()
      })
  }, [search])

  // TODO: remove this hack
  // useEffect(() => {
  //   if (
  //     inputRef.current &&
  //     selectedOptions.some((o) => !selected.includes(o))
  //   ) {
  //     // Manually fire the input change event for live update form
  //     // https://stackoverflow.com/a/36648958/15425660
  //     inputRef.current.dispatchEvent(new Event('change', { bubbles: true }))
  //   }
  // }, [JSON.stringify(selectedOptions)])

  return (
    <Listbox
      className={'w-full'}
      as='div'
      value={selectedOptions}
      onChange={handleSelect}
    >
      {() => (
        <>
          <SelectButton>
            <div className='flex flex-wrap items-center p-1 rounded-sm text-lg w-full truncate gap-0.5'>
              {selectedOptions.length < 1
                ? 'Select'
                : selectedOptions.map((o) => (
                    <Option
                      key={o}
                      label={o}
                      remove={() => handleDeselect(o)}
                    />
                  ))}

              <input
                className='outline-none'
                value={search}
                ref={searchRef}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </SelectButton>
          <Transition
            as={Fragment}
            leave='transition ease-in duration-100'
            leaveFrom='opacity-100'
            leaveTo='opacity-0'
            // The transition pulls the focus from the input here we put it back
            beforeEnter={() => searchRef.current?.focus()}
          >
            <Listbox.Options className='absolute z-10 text-lg w-full p-1 mt-1 overflow-auto bg-white rounded-md max-h-60 focus:outline-none border border-gray'>
              {loading ? (
                <li className='w-full flex flex-row justify-center items-center'>
                  <i className='fad fa-spinner-third fa-spin' />
                </li>
              ) : (
                <>
                  {options.map((o) => (
                    <SelectOption key={o} value={o}>
                      {({ active }) => {
                        const selected = isSelected(o)
                        return (
                          <>
                            <span
                              className={`${
                                selectedOptions ? 'font-medium' : 'font-normal'
                              } block truncate`}
                            >
                              {o}
                            </span>
                            {selected ? (
                              <span
                                className={`${
                                  active ? 'text-black-50' : 'text-black-20'
                                }
                            absolute inset-y-0 right-0 flex items-center pr-3`}
                              >
                                <i className='fa fa-check w-5 h-5' />
                              </span>
                            ) : null}
                          </>
                        )
                      }}
                    </SelectOption>
                  ))}
                </>
              )}
            </Listbox.Options>
          </Transition>
          <input
            ref={inputRef}
            type='hidden'
            name={name}
            id={`id_${name}`}
            value={selectedOptions.join(',')}
          />
        </>
      )}
    </Listbox>
  )
}

const Option = ({ label, remove }) => (
  <div className='flex flex-row rounded items-center p-2 bg-blue-20'>
    <span className='text-base'>{label}</span>
    <i className='fal fa-times ml-1 fa-xs' onClick={remove} />
  </div>
)

class AutocompleteMultiSelect extends HTMLElement {
  static observedAttributes = ['column']

  attributeChangedCallback() {
    const mountPoint = document.createElement('div')
    // Because the Select dropdown will be absolute positioned we need to make the outer div relative
    mountPoint.setAttribute('class', 'relative w-full')
    const selected = JSON.parse(
      this.querySelector('#selected')?.innerHTML || '[]'
    )

    const parentType = this.attributes['parent-type'].value
    const parentId = this.attributes['parent'].value

    const name = this.attributes['name'].value

    if (this.attributes['column'] === undefined) {
      // column is added by AlpineJS, not available in the initial render
      return
    }

    const column = this.attributes['column'].value

    this.replaceChildren(mountPoint)
    ReactDOM.render(
      <AutocompleteMultiSelect_
        parentType={parentType}
        parentId={parentId}
        name={name}
        selected={selected}
        column={column}
      />,
      mountPoint
    )
  }

  disconnectedCallback() {
    ReactDOM.unmountComponentAtNode(this)
  }
}

export default AutocompleteMultiSelect
