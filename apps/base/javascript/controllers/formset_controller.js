import { Controller } from '@hotwired/stimulus'
import { GyanaEvents } from 'apps/base/javascript/events'
import Sortable from 'sortablejs'

/*
Everytime a form is moved all forms a renumbered in the new order
Elements are sorted by big integers, in reverse numeric order, with the final element
at "0". This enables the backend to add new elements without knowing about
the other elements.
*/

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

    if (this.element.querySelectorAll('input[name*=sort_index]').length) {
      Array.from(this.element.querySelectorAll(this.wrapperSelector)).forEach(
        (el) => el.classList.add('formset-wrapper--grab')
      )
    }

    this.sortable = Sortable.create(this.targetTarget, {
      filter: ".CodeMirror",
      preventOnFilter: false,
      onChoose: (event) => {
        const chosenFormset = this.element.querySelector(`[data-formset-index="${event.oldIndex}"]`)
        const textareaTarget = chosenFormset.querySelector(`[data-codemirror-target="textarea"]`)

        if (textareaTarget) {
          textareaTarget.dataset.codemirrorIgnore = true
        }
      },
      onEnd: (event) => {
        const sortIndexInputs = Array.from(
          this.element.querySelectorAll('input[name*=sort_index]')
        )

        const numInputs = sortIndexInputs.length

        for (const [idx, el] of sortIndexInputs.entries()) {
          el.value = numInputs - idx
        }
      },
    })
  }

  add(e) {
    e.preventDefault()

    const TOTAL_FORMS = this.element.querySelector(
      `#id_${this.prefixValue}-TOTAL_FORMS`
    )
    const total = parseInt(TOTAL_FORMS.value)
    TOTAL_FORMS.value = parseInt(total) + 1

    for (const el of this.element.querySelectorAll('input[name*=sort_index]')) {
      el.value = (BigInt(el.value) + 1n).toString()
    }

    window.dispatchEvent(new CustomEvent(GyanaEvents.UPDATE_FORM_COUNT))
    this.dispatch('add', { event: e })
  }

  remove(e) {
    e.preventDefault()

    const wrapper = e.target.closest(this.wrapperSelector)

    const input = wrapper.querySelector("input[name*='-DELETE']")
    input.checked = true

    wrapper.querySelectorAll('[required]').forEach((el) => {
      el.removeAttribute('required')
    })

    window.dispatchEvent(new CustomEvent(GyanaEvents.UPDATE_FORM_COUNT))
    this.dispatch('remove', { event: e })
  }
}
