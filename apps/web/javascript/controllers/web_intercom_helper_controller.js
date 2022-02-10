import { Controller } from '@hotwired/stimulus'

/**
 * Can be used to show the intercom "bubble" using a different element,
 * if intercom isn't loaded it simply hides the element.
 */
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
