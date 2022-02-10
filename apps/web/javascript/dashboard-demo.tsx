'use strict'
import React from 'react'
import ReactDOM from 'react-dom'
import DashboardDemo from './components/DashboardDemo'

class DashboardDemoWC extends HTMLElement {
  connectedCallback() {
    ReactDOM.render(<DashboardDemo />, this)
  }
  disconnectedCallback() {
    ReactDOM.unmountComponentAtNode(this)
  }
}

customElements.get('dashboard-demo') || customElements.define('dashboard-demo', DashboardDemoWC)
