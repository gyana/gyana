import { Controller } from 'stimulus'

// Open a modal with the content populated by a turbo-frame
export default class extends Controller {
  static targets = ['modal', 'turboFrame', 'closingWarning']

  connect() {
    this.changed = false
    const params = new URLSearchParams(window.location.search)
    if (params.get('modal_item')) {
      this.modalTarget.classList.remove('hidden')
    }
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
    const params = new URLSearchParams(location.search)
    params.set('modal_item', event.target.getAttribute('data-item'))
    history.replaceState({}, '', `${location.pathname}?${params.toString()}`)
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

    const params = new URLSearchParams(location.search)
    params.delete('modal_item')
    history.replaceState(
      {},
      '',
      `${location.pathname}${params.toString() ? '?' + params.toString() : ''}`
    )
  }

  closeWarning() {
    this.closingWarningTarget.classList.add('hidden')
  }

  onInput(event) {
    if (event.key == 'Escape') {
      this.close()
    }
  }

  save() {
    this.changed = false
  }
}
