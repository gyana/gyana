'use strict'
import ErrorState from 'apps/workflows/javascript/components/ErrorState'
import LoadingState from 'apps/workflows/javascript/components/LoadingState'
import { useBlockUntilSchemaReady } from 'apps/workflows/javascript/hooks/useBlockUntilSchemaReady'
import React from 'react'
import ReactDOM from 'react-dom'
import { ReactFlowProvider } from 'react-flow-renderer'
import ScheduleFlow from './components/ScheduleFlow'

interface Props {
  projectId: number
  celeryProgressUrl: string
  runTaskUrl?: string
}

const SafeScheduleFlow: React.FC<Props> = ({ projectId, runTaskUrl, celeryProgressUrl }) => {
  const { finishedPinging, schemaReady } = useBlockUntilSchemaReady()

  return (
    <>
      {schemaReady ? (
        <ScheduleFlow
          projectId={projectId}
          runTaskUrl={runTaskUrl}
          celeryProgressUrl={celeryProgressUrl}
        />
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
    const celeryProgressUrl = this.attributes['celeryProgressUrl'].value
    const runTaskUrl = this.attributes['runTaskUrl']?.value
    ReactDOM.render(
      <ReactFlowProvider>
        <SafeScheduleFlow
          projectId={projectId}
          runTaskUrl={runTaskUrl}
          celeryProgressUrl={celeryProgressUrl}
        />
      </ReactFlowProvider>,
      this
    )
  }
  disconnectedCallback() {
    ReactDOM.unmountComponentAtNode(this)
  }
}

customElements.get('schedule-flow') || customElements.define('schedule-flow', ReactDndFlow)
