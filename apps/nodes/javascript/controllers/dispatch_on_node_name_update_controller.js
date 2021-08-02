import { Controller } from 'stimulus'
import { NODE_NAME_UPDATED_EVENT_PREFIX } from 'apps/utils/javascript/events'

// Manually dispatch event on node name update

export default class extends Controller {
  static values = {
    node: String,
  }

  connect() {
    this.element.addEventListener('submit', () => {
      const value = this.element.querySelector('input[name=name]').value
      window.dispatchEvent(
        new CustomEvent(`${NODE_NAME_UPDATED_EVENT_PREFIX}-${this.nodeValue}`, {
          detail: { value },
        })
      )
    })
  }
}
