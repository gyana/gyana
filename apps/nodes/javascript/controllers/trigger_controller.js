import { Controller } from 'stimulus'

// Trigger an event on click

export default class extends Controller {
  static values = {
    event: String,
  }

  static targets = ['event']

  dispatch(event) {
    const value = this.hasEventTarget ? this.eventTarget.value : null
    window.dispatchEvent(new CustomEvent(this.eventValue, { detail: { value } }))
  }
}
