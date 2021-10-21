import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['input']

  toggle() {
    this.inputTarget.type = this.inputTarget.type === 'password' ? 'text' : 'password'
  }
}
