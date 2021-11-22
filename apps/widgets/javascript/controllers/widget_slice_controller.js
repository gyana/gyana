import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['input', 'addButton', 'removeButton']
  remove() {
    this.inputTarget.classList.add('hidden')
    this.removeButtonTarget.classList.add('hidden')
    this.addButtonTarget.classList.remove('hidden')
    this.inputTarget.options[0].selected = true
  }
  add() {
    this.inputTarget.classList.remove('hidden')
    this.removeButtonTarget.classList.remove('hidden')
    this.addButtonTarget.classList.add('hidden')
  }
}
