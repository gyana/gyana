import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['input', 'addButton', 'control', 'compare']

  remove() {
    this.inputTarget.addAttribute('hidden', '')
    this.addButtonTarget.removeAttribute('hidden')
    this.hasControlTarget && this.controlTarget.addAttribute('hidden', '')
    this.hasCompareTarget && this.compareTarget.addAttribute('hidden', '')
    const select = this.inputTarget.getElementsByTagName('select')[0]
    select.options.selectedIndex = 0
  }

  add() {
    this.inputTarget.removeAttribute('hidden')
    this.addButtonTarget.addAttribute('hidden', '')
    this.hasControlTarget && this.controlTarget.removeAttribute('hidden')
    this.hasCompareTarget && this.compareTarget.removeAttribute('hidden')
  }
}
