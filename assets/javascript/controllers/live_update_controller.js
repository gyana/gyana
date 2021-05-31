import { Controller } from 'stimulus'

export default class extends Controller {
  listener = () => {
    // requestSubmit required for turbo-frame
    this.element.setAttribute('novalidate', '')
    this.element.requestSubmit()
  }

  connect() {
    this.element.addEventListener('change', this.listener)
  }

  update(event) {
    this.element.removeEventListener('change', this.listener)
    this.element.method = 'post'

    // provide information to server on clicked button
    const hidden_input = document.createElement('input')
    hidden_input.setAttribute('type', 'hidden')
    hidden_input.setAttribute('name', event.target.getAttribute('data-name'))
    this.element.appendChild(hidden_input)

    this.element.setAttribute('data-turbo-frame', '_top')

    event.preventDefault()
    event.target.setAttribute('type', 'submit')

    this.element.requestSubmit()
  }
}
