import { Controller } from 'stimulus'

// Reload the Turbo Frame on workflow run event.

const WORKFLOW_RUN_EVENT = 'gyana:run-workflow'

export default class extends Controller {
  refresh() {
    const src = this.element.src
    this.element.removeAttribute('src')
    this.element.innerHTML = 'Loading ...'
    this.element.setAttribute('src', src)
  }

  connect() {
    const refresh = this.refresh.bind(this)
    window.addEventListener(WORKFLOW_RUN_EVENT, refresh)
  }

  disconnect() {
    window.removeEventListener(WORKFLOW_RUN_EVENT, this.refresh)
  }
}
