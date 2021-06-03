import { Controller } from 'stimulus'

// Trigger an event on click

export default class extends Controller {
  static values = {
    event: String,
  }

  dispatch() {
    window.dispatchEvent(new Event(this.eventValue))
  }
}
