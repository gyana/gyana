import { Controller } from 'stimulus'

export default class extends Controller {
  static targets = ['trigger', 'body']
  static values = {
    dontHideBody: String,
    position: String,
  }

  connect() {
    this.element.style.position = 'relative'

    this.listener = function (e) {
      if (!this.element.contains(e.target)) {
        this.bodyTarget.style.display = 'none'
      }
    }

    window.addEventListener('click', this.listener.bind(this))

    if (this.dontHideBodyValue === 'True') {
      this.bodyTarget.style.display = 'block'
    }

    this.bodyTarget.style.position = this.positionValue || 'absolute'
    this.bodyTarget.style.right = 0
  }

  disconnect() {
    window.removeEventListener('click', this.listener)
  }

  trigger(event) {
    this.bodyTarget.style.display = 'block' == this.bodyTarget.style.display ? 'none' : 'block'
  }
}
