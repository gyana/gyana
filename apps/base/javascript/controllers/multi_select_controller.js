import { Controller } from '@hotwired/stimulus'

/**
 * Checkbox group helper controller.
 */
export default class extends Controller {
  static targets = ['control']

  initialize() {
    // Should only be checkboxes
    this.inputElements = this.element.querySelectorAll('input')
  }

  checkAllInputs() {
    this.inputElements.forEach((input) => {
      input.checked = true
    })
  }

  uncheckAllInputs() {
    this.inputElements.forEach((input) => {
      input.checked = false
    })
  }
}
