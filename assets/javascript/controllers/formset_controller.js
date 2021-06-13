import { Controller } from 'stimulus'

// Dynamically add and remove formset in Django
// Inspired by https://github.com/stimulus-components/stimulus-rails-nested-form

export default class extends Controller {
  static targets = ['target', 'template']
  static values = {
    wrapperSelector: String,
  }

  initialize() {
    this.wrapperSelector = this.wrapperSelectorValue || '.formset-wrapper'
  }

  add(e) {
    e.preventDefault()

    const TOTAL_FORMS = this.element.querySelector('#id_filters-TOTAL_FORMS')
    const total = parseInt(TOTAL_FORMS.value)

    const content = this.templateTarget.innerHTML.replace(/__prefix__/g, total)
    this.targetTarget.insertAdjacentHTML('beforeend', content)

    TOTAL_FORMS.value = parseInt(total) + 1
  }

  remove(e) {
    e.preventDefault()

    // @ts-ignore
    const wrapper = e.target.closest(this.wrapperSelector)

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
