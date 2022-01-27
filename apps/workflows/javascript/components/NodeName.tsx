import { GyanaEvents } from 'apps/base/javascript/events'
import React, { useState, useEffect } from 'react'
import { useDebouncedCallback } from 'use-debounce'
import { updateNode } from '../api'

interface Props {
  id: string
  name: string
  placeholder: string
  kind: string
}

const NodeName: React.FC<Props> = ({ id, name, placeholder, kind }) => {
  const [text, setText] = useState(name || '')
  const updateName = useDebouncedCallback(async (name: string) => {
    await updateNode(id, { name })
    if (kind == 'output') {
      window.dispatchEvent(new CustomEvent(`${GyanaEvents.UPDATE_NODE}-${id}`))
    }
  }, 300)

  useEffect(() => {
    if (text !== name) updateName(text)
  }, [text])

  useEffect(() => {
    const eventName = `${GyanaEvents.UPDATE_NODE_NAME}-${id}`

    const updateText = (event) => {
      const { value } = event.detail
      setText(value)
    }

    window.addEventListener(eventName, updateText, false)
    return () => window.removeEventListener(eventName, updateText)
  }, [])

  return (
    <input
      className='input__contenteditable absolute -top-12'
      placeholder={placeholder}
      value={text}
      onChange={(e) => setText(e.target.value)}
    />
  )
}

export default NodeName
