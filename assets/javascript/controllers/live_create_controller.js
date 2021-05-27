import { Controller } from 'stimulus'

export default class extends Controller {
  listener = () => {
    // requestSubmit required for turbo-frame
    this.element.requestSubmit()
  }

  connect() {
    this.element.addEventListener('change', this.listener)
  }

  create() {
    this.element.removeEventListener('change', this.listener)
    this.element.method = 'post'

    this.element.requestSubmit()
  }

  create_preview() {
    // use by the view to add preview query param
    const preview_input = document.createElement('input')
    preview_input.setAttribute('type', 'hidden')
    preview_input.setAttribute('name', 'save-preview')

    this.element.appendChild(preview_input)

    this.create()
  }
}
