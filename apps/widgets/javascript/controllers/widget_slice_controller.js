import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['input', 'addButton']
  remove() {
    this.inputTarget.classList.add('hidden')
    this.addButtonTarget.classList.remove('hidden')
    const select = this.inputTarget.getElementsByTagName('select')[0]
    select.options.selectedIndex = 0
  }
  add() {
    this.inputTarget.classList.remove('hidden')
    this.addButtonTarget.classList.add('hidden')
  }
}
