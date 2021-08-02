import { Controller } from 'stimulus'
import { WORKFLOW_UPDATED_EVENT, NODE_UPDATED_EVENT_PREFIX } from 'apps/utils/javascript/events'

// Manually dispatch events when the node is updated

export default class extends Controller {
  static values = {
    node: String,
  }

  connect() {
    this.element.addEventListener('submit', () => {
      window.dispatchEvent(new CustomEvent(WORKFLOW_UPDATED_EVENT))
      window.dispatchEvent(new CustomEvent(`${NODE_UPDATED_EVENT_PREFIX}-${this.nodeValue}`))
    })
  }
}
