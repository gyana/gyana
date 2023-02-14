import { Controller } from '@hotwired/stimulus'
import { GyanaEvents } from 'apps/base/javascript/events'

/**
 * Adds event listeners to node forms in order to dispatch React events.
 * Syncs react and HTML states.
 */
export default class extends Controller {
  static values = {
    id: String,
  }

  connect() {
    this.element.querySelector('#node-update-form').addEventListener('submit', () => {
      this.sendNodeEvents()
    })

    this.element.querySelector('#node-name-update-form').addEventListener('submit', (event) => {
      window.dispatchEvent(
        new CustomEvent(`${GyanaEvents.UPDATE_NODE_NAME}-${this.idValue}`, {
          detail: { value: event.target.querySelector('input[name=name]').value },
        })
      )
    })
  }

  sendNodeEvents() {
    window.dispatchEvent(new CustomEvent(GyanaEvents.UPDATE_WORKFLOW))
    window.dispatchEvent(new CustomEvent(`${GyanaEvents.UPDATE_NODE}-${this.idValue}`))
  }
}
