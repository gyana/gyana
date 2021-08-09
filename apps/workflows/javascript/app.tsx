'use strict'
import React, { useEffect, useState } from 'react'
import ReactDOM from 'react-dom'
import { ReactFlowProvider } from 'react-flow-renderer'
import DnDFlow from './dnd-flow'

let auth = new coreapi.auth.SessionAuthentication({
  csrfCookieName: 'csrftoken',
  csrfHeaderName: 'X-CSRFToken',
})

let client = new coreapi.Client({ auth: auth })

const Canvas: React.FC<{ client: coreapi.Client; workflowId: number }> = ({
  client,
  workflowId,
}) => {
  const [_, setHasSchema] = useState(false)

  useEffect(() => {
    const checkSchemaExists = async () => {
      while (!window.schema) {
        await new Promise((resolve) => setTimeout(resolve, 200))
      }
      setHasSchema(true)
    }
    checkSchemaExists()
  }, [])

  if (window.schema) return <DnDFlow client={client} workflowId={workflowId} />

  return (
    <div className='dndflow'>
      <div className='placeholder-scr placeholder-scr--fillscreen'>
        <i className='placeholder-scr__icon fad fa-spinner-third fa-spin'></i>
      </div>
    </div>
  )
}

class ReactDndFlow extends HTMLElement {
  connectedCallback() {
    const workflowId = this.attributes['workflowId'].value
    ReactDOM.render(
      <ReactFlowProvider>
        <Canvas client={client} workflowId={workflowId} />
      </ReactFlowProvider>,
      this
    )
  }
}

customElements.get('dnd-flow') || customElements.define('dnd-flow', ReactDndFlow)
