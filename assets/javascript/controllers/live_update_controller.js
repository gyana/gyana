import { Controller } from 'stimulus'
import morphdom from 'morphdom'

export default class extends Controller {
  listener = async () => {
    // manually POST the form and get HTML response
    const data = new FormData(this.element)
    const result = await fetch(this.element.action, {
      method: 'POST',
      body: data,
    })
    const text = await result.text()

    // Extract the form element and morph into the DOM
    const parser = new DOMParser()
    const doc = parser.parseFromString(text, 'text/html')
    const newForm = doc.querySelector('form')
    morphdom(this.element, newForm)
  }

  connect() {
    this.element.addEventListener('change', this.listener)
  }
}
