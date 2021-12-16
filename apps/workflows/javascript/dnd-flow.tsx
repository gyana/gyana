'use strict'
import React from 'react'
import ReactDOM from 'react-dom'
import { ReactFlowProvider } from 'react-flow-renderer'
import DnDFlow from './components/DnDFlow'
import ErrorState from 'apps/base/javascript/components/ErrorState'
import LoadingState from 'apps/base/javascript/components/LoadingState'
import { useBlockUntilSchemaReady } from 'apps/base/javascript/hooks/useBlockUntilSchemaReady'

interface Props {
  workflowId: number
}

const SafeDnDFlow: React.FC<Props> = ({ workflowId }) => {
  const { finishedPinging, schemaReady } = useBlockUntilSchemaReady()

  return (
    <>
      {schemaReady ? (
        <DnDFlow workflowId={workflowId} />
      ) : !finishedPinging ? (
        <LoadingState />
      ) : (
        <ErrorState error='Something went wrong!' />
      )}
    </>
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
