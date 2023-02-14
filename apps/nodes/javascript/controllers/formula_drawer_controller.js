import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['htmx', 'drawer']

  open(e) {
    const src = new URL(
      location.origin + this.htmxTarget.getAttribute('data-modal-src')
    )
    this.htmxTarget.innerHTML = `
        <div class='placeholder-scr placeholder-scr--fillscreen'>
          <i class='placeholder-scr__icon fad fa-spinner-third fa-spin fa-2x'></i>
        </div>
      `
    src.searchParams.set(
      'function',
      e.currentTarget.getAttribute('data-modal-src')
    )
    this.htmxTarget.setAttribute(
      'hx-get',
      `${src.pathname}?${src.searchParams.toString()}`
    )
    this.drawerTarget.classList.remove('closed')

    htmx.process(this.htmxTarget)
    this.htmxTarget.dispatchEvent(new CustomEvent('hx-formula-draw-load'))
  }

  close() {
    this.drawerTarget.classList.add('closed')
  }
}
