'use strict'
import ErrorState from 'apps/base/javascript/components/ErrorState'
import LoadingState from 'apps/base/javascript/components/LoadingState'
import { useBlockUntilSchemaReady } from 'apps/base/javascript/hooks/useBlockUntilSchemaReady'
import React from 'react'
import ReactDOM from 'react-dom'
import { ReactFlowProvider } from 'react-flow-renderer'
import AutomateFlow from './components/AutomateFlow'

interface Props {
  projectId: number
}

const SafeAutomateFlow: React.FC<Props> = ({ projectId }) => {
  const { finishedPinging, schemaReady } = useBlockUntilSchemaReady()

  return (
    <>
      {schemaReady ? (
        <AutomateFlow projectId={projectId} />
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
    const projectId = this.attributes['projectId'].value
    ReactDOM.render(
      <ReactFlowProvider>
        <SafeAutomateFlow projectId={projectId} />
      </ReactFlowProvider>,
      this
    )
  }
  disconnectedCallback() {
    ReactDOM.unmountComponentAtNode(this)
  }
}

customElements.get('automate-flow') || customElements.define('automate-flow', ReactDndFlow)
