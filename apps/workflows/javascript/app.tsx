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
      <div className='placeholder-scr placeholder-scr--fillscreen'>
        {finishedPinging ? (
          <div className='flex flex-col items-center'>
            <i className='fa fa-exclamation-triangle text-red fa-4x mb-3'></i>
            <p>Something went wrong!</p>
            <p>
              Contact{' '}
              <a className='link' href='mailto: support@gyana.com'>
                support@gyana.com
              </a>{' '}
              for support.
            </p>
            <p>
              Or try reloading{' '}
              <button onClick={() => window.location.reload()}>
                <i className='far fa-sync text-blue'></i>
              </button>
            </p>
          </div>
        ) : (
          <>
            <i className='placeholder-scr__icon fad fa-spinner-third fa-spin fa-3x'></i>
            <span>Loading</span>
          </>
        )}
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
