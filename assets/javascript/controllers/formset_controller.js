import { Controller } from 'stimulus'

// Dynamically add and remove formset in Django
// Inspired by https://github.com/stimulus-components/stimulus-rails-nested-form

export default class extends Controller {
  static targets = ['target', 'template']
  static values = {
    wrapperSelector: String,
    prefix: String,
  }

  initialize() {
    this.wrapperSelector = this.wrapperSelectorValue || '.formset-wrapper'
  }

  add(e) {
    e.preventDefault()

    const TOTAL_FORMS = this.element.querySelector(`#id_${this.prefixValue}-TOTAL_FORMS`)
    const total = parseInt(TOTAL_FORMS.value)

    // The HTML <template> is an empty form with a __prefix__ placeholder for the index

    const content = this.templateTarget.innerHTML.replace(/__prefix__/g, total)
    this.targetTarget.insertAdjacentHTML('beforeend', content)

    // Increment the total forms index, for consistency with live update form

    TOTAL_FORMS.value = parseInt(total) + 1
  }

  remove(e) {
    e.preventDefault()

    const wrapper = e.target.closest(this.wrapperSelector)

    // If the field has `data-new-record` set, then it was added dynamically. Otherwise we
    // need to "check" the hidden delete input. Django will then delete it on the post request.

    if (wrapper.dataset.newRecord === 'true') {
      wrapper.remove()
    } else {
      wrapper.style.display = 'none'

      const input = wrapper.querySelector("input[name*='-DELETE']")
      input.value = 'on'
      input.setAttribute('checked', '')
    }
  }
}
