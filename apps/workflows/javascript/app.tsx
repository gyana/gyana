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

const PAUSE = 200
const MAX_TIME = 5000
const Canvas: React.FC<{ client: coreapi.Client; workflowId: number }> = ({
  client,
  workflowId,
}) => {
  const [finishedPinging, setFinishedPinging] = useState(false)

  useEffect(() => {
    const checkSchemaExists = async () => {
      for (let time = 0; time < MAX_TIME; time += PAUSE) {
        if (window.schema) break
        await new Promise((resolve) => setTimeout(resolve, PAUSE))
      }
      setFinishedPinging(true)
    }
    checkSchemaExists()
  }, [])

  if (window.schema) return <DnDFlow client={client} workflowId={workflowId} />

  return (
    <div className='dndflow'>
      {finishedPinging ? (
        <span>Something went wrong</span>
      ) : (
        <div className='placeholder-scr placeholder-scr--fillscreen'>
          <i className='placeholder-scr__icon fad fa-spinner-third fa-spin'></i>
        </div>
      )}
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
