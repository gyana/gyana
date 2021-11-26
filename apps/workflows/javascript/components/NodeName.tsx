import { GyanaEvents } from 'apps/base/javascript/events'
import React, { useState, useEffect } from 'react'
import { useDebouncedCallback } from 'use-debounce'
import { getApiClient } from 'apps/base/javascript/api'

const client = getApiClient()

interface Props {
  name: string
  id: string
}

const NodeName: React.FC<Props> = ({ name, id }) => {
  const [text, setText] = useState(name)
  const updateName = useDebouncedCallback((name: string) => {
    client.action(window.schema, ['nodes', 'api', 'nodes', 'partial_update'], {
      id,
      name,
    }),
      300
  })

  useEffect(() => {
    text !== name && updateName(text)
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
      value={text}
      onChange={(e) => setText(e.target.value)}
    />
  )
}

export default NodeName
