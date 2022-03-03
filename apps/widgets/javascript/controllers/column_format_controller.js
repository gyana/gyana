import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['inputs', 'hiddenInput', 'button']
  handle() {
    if (this.inputsTarget.hasAttribute('hidden')) {
      this.hiddenInputTarget.checked = false
      this.inputsTarget.removeAttribute('hidden')
      this.buttonTarget.classList.add('link--unfolded')
    } else {
      this.inputsTarget.setAttribute('hidden', '')
      this.hiddenInputTarget.checked = true
      this.buttonTarget.classList.remove('link--unfolded')
    }
  }
}
