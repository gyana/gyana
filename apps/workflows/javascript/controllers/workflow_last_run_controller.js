import { Controller } from 'stimulus'
import { GyanaEvents } from 'apps/utils/javascript/events'

// Reload the Turbo Frame on workflow run event.

export default class extends Controller {
  refresh() {
    const frame = this.element.querySelector('turbo-frame')
    const src = frame.src
    frame.removeAttribute('src')
    frame.innerHTML = 'Loading ...'
    frame.setAttribute('src', src)
  }

  connect() {
    const refresh = this.refresh.bind(this)
    window.addEventListener(GyanaEvents.RUN_WORKFLOW, refresh)
  }

  disconnect() {
    window.removeEventListener(GyanaEvents.RUN_WORKFLOW, this.refresh)
  }
}
