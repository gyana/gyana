import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  trigger() {
    if ('Intercom' in window) window.Intercom('show')
  }

  connect() {
    if (!('Intercom' in window)) {
      this.element.style.display = 'none'
    }
  }
}
