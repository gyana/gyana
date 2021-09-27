import { Controller } from 'stimulus'

// Add loading indicator on form submission

export default class extends Controller {
  onSubmit(event) {
    // https://turbo.hotwired.dev/reference/events
    const submitter = event.submitter || event.detail.formSubmission.submitter

    // event fires twice for top level forms with data-turbo="true" (default)
    if (submitter && !submitter.disabled && !(submitter.getAttribute('data-loading-false') == '')) {
      submitter.innerHTML = '<i class="placeholder-scr__icon fad fa-spinner-third fa-spin"></i>'
      for (const el of event.target.querySelectorAll('button[type=submit]')) el.disabled = true
    }
  }

  connect() {
    document.addEventListener('submit', this.onSubmit) // data-turbo="false" and root level forms
    document.addEventListener('turbo:submit-start', this.onSubmit) // submissions within turbo-frames
  }

  disconnect() {
    document.addEventListener('submit', this.onSubmit)
    document.removeEventListener('turbo:submit-start', this.onSubmit)
  }
}
