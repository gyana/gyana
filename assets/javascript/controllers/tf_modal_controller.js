import { Controller } from 'stimulus'

// Open a modal with the content populated by a turbo-frame

export default class extends Controller {
  static targets = ['modal', 'turboFrame', 'closingWarning']

  connect() {
    this.changed = false
  }

  open(event) {
    if (event.target.getAttribute('data-src') !== this.turboFrameTarget.getAttribute('src')) {
      this.turboFrameTarget.innerHTML = `
        <div class='placeholder-scr placeholder-scr--fillscreen'>
          <i class='placeholder-scr__icon fad fa-spinner-third fa-spin fa-3x'></i>
        </div>
      `
      this.turboFrameTarget.setAttribute('src', event.target.getAttribute('data-src'))
    }

    this.modalTarget.classList.remove('hidden')
  }

  change() {
    this.changed = true
  }

  close() {
    if (this.changed) {
      this.closingWarningTarget.classList.remove('hidden')
    } else {
      this.forceClose()
    }
  }

  forceClose() {
    this.changed = false
    this.modalTarget.classList.add('hidden')
  }

  closeWarning() {
    this.closingWarningTarget.classList.add('hidden')
  }

  onInput(event) {
    if (event.key == 'Escape') {
      this.modalTarget.classList.add('hidden')
    }
  }

  save() {
    this.changed = false
  }
}
