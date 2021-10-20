import { Controller } from '@hotwired/stimulus'
import { getApiClient } from 'apps/base/javascript/api'

export default class extends Controller {
  static targets = ['close']

  connect() {
    // remove element after the css transition.
    setTimeout(() => {
      if (this.element) {
        this.element.remove()
      }
    }, 5550)
  }

  close() {
    this.element.remove()
  }
}
