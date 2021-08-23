import { Controller } from 'stimulus'

// Add loading indicator on form submission

export default class extends Controller {
  onSubmit(event) {
    console.error('SUBMIT')
    for (const el of event.target.querySelectorAll('button[type=submit]')) {
      el.disabled = true
      el.innerHTML = '<i class="placeholder-scr__icon fad fa-spinner-third fa-spin"></i>'
    }
  }

  connect() {
    document.addEventListener('submit', this.onSubmit)
  }

  disconnect() {
    document.removeEventListener('submit', this.onSubmit)
  }
}
