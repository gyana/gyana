import { Controller } from '@hotwired/stimulus'

// Trigger an event on click

export default class extends Controller {
  static targets = ['input', 'label']

  select(event) {
    const currentTarget = event.currentTarget
    this.inputTarget.value = currentTarget.id

    // Remove css from previous selected target
    this.labelTargets.forEach((label) => {
      label.className = label.className.replace('checkbox__checked', '')
    })

    // Add css to now selected element
    currentTarget.className += 'checkbox__checked'
  }
}
