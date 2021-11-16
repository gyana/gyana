import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['turboFrame', 'drawer']

  open(e) {
    const src = new URL(location.origin + this.turboFrameTarget.getAttribute('src'))
    this.turboFrameTarget.removeAttribute('src')
    this.turboFrameTarget.innerHTML = `
        <div class='placeholder-scr placeholder-scr--fillscreen'>
          <i class='placeholder-scr__icon fad fa-spinner-third fa-spin fa-2x'></i>
        </div>
      `
    src.searchParams.set('function', e.currentTarget.getAttribute('data-src'))
    this.turboFrameTarget.setAttribute('src', `${src.pathname}?${src.searchParams.toString()}`)
    this.drawerTarget.classList.remove('closed')
  }

  close() {
    this.drawerTarget.classList.add('closed')
  }
}
