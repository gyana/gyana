'use strict'
import React from 'react'
import ReactDOM from 'react-dom'
import { ReactFlowProvider } from 'react-flow-renderer'
import DnDFlow from './components/DnDFlow'
import ErrorState from './components/ErrorState'
import LoadingState from './components/LoadingState'
import { useBlockUntilSchemaReady } from './hooks/useBlockUntilSchemaReady'

interface Props {
  workflowId: number
}

const SafeDnDFlow: React.FC<Props> = ({ workflowId }) => {
  const { finishedPinging, schemaReady } = useBlockUntilSchemaReady()

  if (schemaReady) return <DnDFlow workflowId={workflowId} />

  return (
    <div className='dndflow'>
      {finishedPinging ? <ErrorState error='Something went wrong!' /> : <LoadingState />}
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
