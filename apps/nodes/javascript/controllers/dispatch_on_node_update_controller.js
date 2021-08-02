import { Controller } from 'stimulus'

// Manually dispatch events when the node is updated

const WORKFLOW_UPDATED_EVENT = 'gyana:update-workflow'
const NODE_UPDATED_EVENT_PREFIX = 'gyana:update-node'

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
