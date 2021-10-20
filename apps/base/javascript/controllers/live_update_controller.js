import { Controller } from '@hotwired/stimulus'
import morphdom from 'morphdom'

const get_formset_row = (element) => element.closest('[data-formset-index]')

export default class extends Controller {
  static targets = ['loading']
  clicked_button = false
  disable = (event) => {
    const form = this.element

    let flag_disabled = false

    const formset_row = get_formset_row(event.target)

    // Disable editing on all elements *after* the edited element
    // Skip non-hidden elements (typically within web components)
    // For formsets, only disable within that row
    // But always disable the submit buttons

    for (const element of form.elements) {
      if (flag_disabled && formset_row && get_formset_row(element) !== formset_row)
        flag_disabled = false

      // TODO: This makes it necessary to double click Save & Preview
      // When clicking shifts focus from an input field
      if (element.type === 'submit' || (flag_disabled && element.type !== 'hidden'))
        element.disabled = true

      if (element === event.target) flag_disabled = true
    }
  }

  listener = async (event) => {
    if (this.clicked_button) return
    if (event.target.hasAttribute('data-live-update-ignore')) return
    const form = this.element

    // manually POST the form and get HTML response
    const data = new FormData(form)
    // HTML forms just omit unchecked checkboxes
    // https://developer.mozilla.org/en-US/docs/Web/API/FormData/FormData
    // which for us iss indistinguishable from the field not being rendered
    // So we add the fields to the form data manually
    form
      .querySelectorAll('input[type=checkbox]:not([data-live-update-ignore]):not(:checked)')
      .forEach((el) => {
        data.append(el.name, false)
      })

    this.loadingTarget.classList.remove('hidden')

    this.disable(event)

    const result = await fetch(form.action, {
      method: 'POST',
      body: data,
    })
    const text = await result.text()

    // Extract the form element and morph into the DOM
    const parser = new DOMParser()
    const doc = parser.parseFromString(text, 'text/html')
    const newForm = doc.querySelector(`#${this.element.id}`)

    morphdom(form, newForm, {
      // https://github.com/patrick-steele-idem/morphdom/issues/16#issuecomment-132630185
      onBeforeElUpdated: function (fromEl, toEl) {
        if (toEl.tagName === 'INPUT') {
          toEl.value = fromEl.value
        }

        if (toEl.tagName === 'TEMPLATE') {
          fromEl.innerHTML = toEl.innerHTML
          return false
        }

        // Do not overwrite web component
        // TODO: Replace the entire node to re-trigger connectedCallback
        if (toEl.tagName.includes('-')) {
          return false
        }
      },
    })

    this.clicked_button = false
    this.loadingTarget.classList.add('hidden')
  }

  connect() {
    this.element.addEventListener('change', this.listener)
    this.element.addEventListener('mousedown', (event) => {
      this.clicked_button = event.target.nodeName == 'BUTTON'
    })
  }
}
