import { Controller } from 'stimulus'
import morphdom from 'morphdom'

export default class extends Controller {
  listener = async () => {
    // requestSubmit required for turbo-frame
    const data = new FormData(this.element)
    const result = await fetch(this.element.action, {
      method: 'POST',
      body: data,
    })
    const text = await result.text()

    const parser = new DOMParser()
    const doc = parser.parseFromString(text, 'text/html')

    const newForm = doc.querySelector('form')

    morphdom(this.element, newForm)
  }

  connect() {
    this.element.addEventListener('change', this.listener)
  }

  update(event) {
    this.element.removeEventListener('change', this.listener)

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
