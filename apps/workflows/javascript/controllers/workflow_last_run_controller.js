import { Controller } from 'stimulus'
import { GyanaEvents } from 'apps/utils/javascript/events'

// Reload the Turbo Frame on workflow run event.

export default class extends Controller {
  static values = {
    src: String,
  }

  refresh() {
    const frame = this.element.querySelector('turbo-frame')
    frame.removeAttribute('src')
    frame.innerHTML = 'Loading ...'
    frame.setAttribute('src', this.srcValue)
  }

  connect() {
    const refresh = this.refresh.bind(this)
    window.addEventListener(GyanaEvents.RUN_WORKFLOW, refresh)
  }

  disconnect() {
    window.removeEventListener(GyanaEvents.RUN_WORKFLOW, this.refresh)
  }
}
