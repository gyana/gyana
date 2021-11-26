import { GyanaEvents } from 'apps/base/javascript/events'
import React, { useContext, useState, useEffect } from 'react'
import { getApiClient } from 'apps/base/javascript/api'
import { DnDContext, IDnDContext } from '../context'

const client = getApiClient()

const NodeDescription = ({ id, data }) => {
  const { workflowId } = useContext(DnDContext) as IDnDContext

  const [description, setDescription] = useState()

  const onNodeConfigUpdate = async () => {
    const result = await client.action(window.schema, ['nodes', 'api', 'nodes', 'read'], {
      workflow: workflowId,
      id,
    })

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
