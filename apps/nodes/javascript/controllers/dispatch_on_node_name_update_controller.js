import { Controller } from 'stimulus'

// Manually dispatch event on node name update

const NODE_NAME_UPDATED_EVENT_PREFIX = 'gyana:update-node-name'

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
