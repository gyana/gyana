import { Controller } from '@hotwired/stimulus'
import { GyanaEvents } from 'apps/base/javascript/events'

// Dispatch events for the React App when the node name or config is updated

export default class extends Controller {
  static values = {
    id: String,
  }

  sendNodeEvents() {
    window.dispatchEvent(new CustomEvent(GyanaEvents.UPDATE_WORKFLOW))
    window.dispatchEvent(new CustomEvent(`${GyanaEvents.UPDATE_NODE}-${this.idValue}`))
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
}
