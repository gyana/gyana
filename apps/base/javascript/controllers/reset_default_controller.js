import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static values = {
    initial: String
  }

  initialize() {

  }

  connect() {

  }

  reset(event) {
    this.element.querySelector("input").value = this.initialValue
    event.currentTarget.classList.add("hidden")
  }
}
