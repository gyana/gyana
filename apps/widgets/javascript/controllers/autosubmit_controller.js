import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['selected']

  connect() {
    if (this.hasSelectedTarget) {
      this.selectedTarget.setAttribute('selected', '')
    }
  }

  onchange() {
    this.element.submit()
  }
}
