'use strict'
import React from 'react'
import ReactDOM from 'react-dom'
import { ReactFlowProvider } from 'react-flow-renderer'
import DnDFlow from './components/DnDFlow'
import { useBlockUntilSchemaReady } from './hooks/useBlockUntilSchemaReady'

interface Props {
  workflowId: number
}

const SafeDnDFlow: React.FC<Props> = ({ workflowId }) => {
  const { finishedPinging, schemaReady } = useBlockUntilSchemaReady()

  if (schemaReady) return <DnDFlow workflowId={workflowId} />

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
            <i className='placeholder-scr__icon fad fa-spinner-third fa-spin fa-2x'></i>
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
        <SafeDnDFlow workflowId={workflowId} />
      </ReactFlowProvider>,
      this
    )
  }
  disconnectedCallback() {
    ReactDOM.unmountComponentAtNode(this)
  }
}

customElements.get('dnd-flow') || customElements.define('dnd-flow', ReactDndFlow)
