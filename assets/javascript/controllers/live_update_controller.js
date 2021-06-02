import { Controller } from 'stimulus'
import morphdom from 'morphdom'

export default class extends Controller {
  listener = async (event) => {
    const form = this.element

    // manually POST the form and get HTML response
    const data = new FormData(form)

    let disabled = false

    // disable editing on all following elements elements
    for (const element of form.elements) {
      if (disabled) element.disabled = true
      if (element === event.target) disabled = true
    }

    const result = await fetch(form.action, {
      method: 'POST',
      body: data,
    })
    const text = await result.text()

    // Extract the form element and morph into the DOM
    const parser = new DOMParser()
    const doc = parser.parseFromString(text, 'text/html')
    const newForm = doc.querySelector('form')
    morphdom(form, newForm, {
      // https://github.com/patrick-steele-idem/morphdom/issues/16#issuecomment-132630185
      onBeforeMorphEl: function (fromEl, toEl) {
        if (toEl.tagName === 'INPUT') {
          toEl.value = fromEl.value
        }
      },
    })
  }

  connect() {
    this.element.addEventListener('change', this.listener)
  }
}
