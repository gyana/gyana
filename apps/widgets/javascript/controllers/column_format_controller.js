import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['inputs', 'hiddenInput', 'button']
  handle() {
    if (this.inputsTarget.classList.contains('hidden')) {
      this.hiddenInputTarget.checked = false
      this.inputsTarget.classList.remove('hidden')
      this.buttonTarget.classList.add('link--unfolded')
    } else {
      this.inputsTarget.classList.add('hidden')
      this.hiddenInputTarget.checked = true
      this.buttonTarget.classList.remove('link--unfolded')
    }
  }
}
