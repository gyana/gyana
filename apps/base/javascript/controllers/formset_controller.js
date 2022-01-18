import { Controller } from '@hotwired/stimulus'
import { GyanaEvents } from 'apps/base/javascript/events'

// Dynamically add and remove formset in Django
// Inspired by https://github.com/stimulus-components/stimulus-rails-nested-form

export default class extends Controller {
  static targets = ['target', 'template']
  static values = {
    wrapperSelector: String,
    prefix: String,
  }

  connect() {
    this.wrapperSelector = this.wrapperSelectorValue || '.formset-wrapper'
  }

  add(e) {
    e.preventDefault()
    const TOTAL_FORMS = this.element.querySelector(`#id_${this.prefixValue}-TOTAL_FORMS`)
    const total = parseInt(TOTAL_FORMS.value)

    TOTAL_FORMS.value = parseInt(total) + 1
    window.dispatchEvent(new CustomEvent(GyanaEvents.UPDATE_FORM_COUNT))
    this.dispatch('add', { event: e })
  }

  remove(e) {
    e.preventDefault()

    const wrapper = e.target.closest(this.wrapperSelector)

    const input = wrapper.querySelector("input[name*='-DELETE']")
    input.value = 'on'

    const TOTAL_FORMS = this.element.querySelector(`#id_${this.prefixValue}-TOTAL_FORMS`)
    const total = parseInt(TOTAL_FORMS.value)

    TOTAL_FORMS.value = parseInt(total) - 1

    wrapper.querySelectorAll('[required]').forEach((el) => {
      el.removeAttribute('required')
    })

    window.dispatchEvent(new CustomEvent(GyanaEvents.UPDATE_FORM_COUNT))
    this.dispatch('remove', { event: e })
  }
}
