'use strict'
import React from 'react'
import ReactDOM from 'react-dom'
import { ReactFlowProvider } from 'react-flow-renderer'
import DnDFlow from './dnd-flow'

let auth = new coreapi.auth.SessionAuthentication({
  csrfCookieName: 'csrftoken',
  csrfHeaderName: 'X-CSRFToken',
})

let client = new coreapi.Client({ auth: auth })
class ReactDndFlow extends HTMLElement {
  connectedCallback() {
    const workflowId = this.attributes['workflowId'].value
    ReactDOM.render(
      <ReactFlowProvider>
        <DnDFlow client={client} workflowId={workflowId} />
      </ReactFlowProvider>,
      this
    )
  }
}

customElements.get('dnd-flow') || customElements.define('dnd-flow', ReactDndFlow)
