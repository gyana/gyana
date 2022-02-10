'use strict'
import React from 'react'
import ReactDOM from 'react-dom'
import IntegrationDemo from './components/IntegrationDemo'

class IntegrationDemoWC extends HTMLElement {
  connectedCallback() {
    ReactDOM.render(<IntegrationDemo />, this)
  }
  disconnectedCallback() {
    ReactDOM.unmountComponentAtNode(this)
  }
}

customElements.get('integration-demo') ||
  customElements.define('integration-demo', IntegrationDemoWC)
