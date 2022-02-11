import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['input', 'addButton', 'control', 'compare']
  remove() {
    this.inputTarget.classList.add('hidden')
    this.addButtonTarget.classList.remove('hidden')
    this.controlTarget.classList.add('hidden')
    this.compareTarget.classList.add('hidden')
    const select = this.inputTarget.getElementsByTagName('select')[0]
    select.options.selectedIndex = 0
  }
  add() {
    this.inputTarget.classList.remove('hidden')
    this.controlTarget.classList.remove('hidden')
    this.compareTarget.classList.remove('hidden')
    this.addButtonTarget.classList.add('hidden')
  }
}
