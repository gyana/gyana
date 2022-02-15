import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['inputs']
  handle() {
    if (this.inputsTarget.classList.contains('hidden')) {
      this.inputsTarget.classList.remove('hidden')
    } else {
      this.inputsTarget.classList.add('hidden')
    }
  }
}
