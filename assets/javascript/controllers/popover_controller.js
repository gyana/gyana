import { Controller } from 'stimulus'

export default class extends Controller {
  static targets = ['trigger', 'body']
  static values = {
    dontHideBody: String,
  }

  connect() {
    this.element.style.position = 'relative'
    this.element.style.display = 'inline-block'

    const bodyTarget = this.bodyTarget
    this.listener = function (e) {
      if (!bodyTarget.contains(e.target)) {
        bodyTarget.style.display = 'none'
      }
    }

    window.addEventListener('click', this.listener)

    if (this.dontHideBodyValue !== 'True') {
      this.bodyTarget.style.display = 'none'
    }

    this.bodyTarget.style.position = 'absolute'
    this.bodyTarget.style.right = 0
  }

  disconnect() {
    window.removeEventListener('click', this.listener)
  }

  trigger(event) {
    event.stopPropagation()
    this.bodyTarget.style.display = 'block' == this.bodyTarget.style.display ? 'none' : 'block'
  }
}
