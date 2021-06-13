import { Controller } from 'stimulus'

// Dynamically add and remove formset in Django
// Inspired by https://github.com/stimulus-components/stimulus-rails-nested-form

export default class extends Controller {
  static targets = ['target', 'template']

  add(e) {
    e.preventDefault()

    const TOTAL_FORMS = this.element.querySelector('#id_filters-TOTAL_FORMS')
    const total = parseInt(TOTAL_FORMS.value)

    const content = this.templateTarget.innerHTML.replace(/__prefix__/g, total)
    this.targetTarget.insertAdjacentHTML('beforeend', content)

    TOTAL_FORMS.value = parseInt(total) + 1
  }
}
