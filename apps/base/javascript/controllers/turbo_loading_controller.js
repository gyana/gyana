import { Controller } from '@hotwired/stimulus'

export default class extends Controller {

  initialize() {
    this.boundHandleTurboClick = this.handleTurboClick.bind(this)
  }

  connect() {
    window.addEventListener('turbo:click', this.boundHandleTurboClick)
  }

  disconnect() {
    window.removeEventListener('turbo:click', this.boundHandleTurboClick)
  }

  handleTurboClick(event) {
    if (event.target.dataset.turboLoading || event.target.dataset.turboLoading == '') {
      const frame = document.querySelector(`turbo-frame[src*="${event.detail.url}"]`)

      frame.style.position = "relative"
      frame.appendChild(this.createPlaceholder())
    }
  }

  createPlaceholder() {
    const placeholder = document.createElement('template')
    placeholder.innerHTML = `
      <div class='placeholder-scr placeholder-scr--overlay'>
        <i class="placeholder-scr__icon fad fa-spinner-third fa-spin"></i>
      </div>
    `.trim()
    return placeholder.content.firstChild
  }
}
