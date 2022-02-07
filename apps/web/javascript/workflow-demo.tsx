'use strict'
import React from 'react'
import ReactDOM from 'react-dom'
import { ReactFlowProvider } from 'react-flow-renderer'
import WorkflowDemo from './components/WorkflowDemo'

class WorkflowDemoWC extends HTMLElement {
  connectedCallback() {
    ReactDOM.render(
      <ReactFlowProvider>
        <WorkflowDemo />
      </ReactFlowProvider>,
      this
    )
  }
  disconnectedCallback() {
    ReactDOM.unmountComponentAtNode(this)
  }
}

customElements.get('workflow-demo') || customElements.define('workflow-demo', WorkflowDemoWC)
