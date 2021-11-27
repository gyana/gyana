import { GyanaEvents } from 'apps/base/javascript/events'
import React, { useState, useEffect } from 'react'
import { getNode } from '../api'

const NodeDescription = ({ id, data }) => {
  const [description, setDescription] = useState()

  const onNodeConfigUpdate = async () => {
    const result = await getNode(id)
    setDescription(result.description)
  }

  useEffect(() => {
    const eventName = `${GyanaEvents.UPDATE_NODE}-${id}`
    window.addEventListener(eventName, onNodeConfigUpdate, false)
    return () => window.removeEventListener(eventName, onNodeConfigUpdate)
  }, [])

  return (
    <p title={description || data.description} className='text-xs overflow-hidden'>
      {description || data.description}
    </p>
  )
}

export default NodeDescription
