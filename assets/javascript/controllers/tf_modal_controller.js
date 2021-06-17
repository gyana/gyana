import { Controller } from 'stimulus'

// Open a modal with the content populated by a turbo-frame

export default class extends Controller {
  static targets = ['modal', 'turboFrame']

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

  close() {
    this.modalTarget.classList.add('hidden')
  }

  onInput(event) {
    if (event.key == 'Escape') {
      this.modalTarget.classList.add('hidden')
    }
  }
}
