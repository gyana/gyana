import { Controller } from '@hotwired/stimulus'
import { GyanaEvents } from 'apps/base/javascript/events'
import Sortable from 'sortablejs'

/*
Get the new sort index for each element, based on the insertion index.

Elements are sorted by big integers, in reverse numeric order, with the final element
at "0". This enables the backend to add new elements without knowing about
the other elements.
*/

const getSortOrder = (sortOrder, idx) => {
  if (idx === 0) {
    // prepend to start of array with +1n
    return [sortOrder[1] + 1n, ...sortOrder.slice(1)]
  } else if (idx === sortOrder.length - 1) {
    // append with 0n, shift everything else back by +1n
    return [...sortOrder.slice(0, -1).map((idx) => idx + 1n), 0n]
  } else {
    // insert, doubling all indexes if required
    let newSortOrder = [...sortOrder]

    if (newSortOrder[idx - 1] - newSortOrder[idx + 1] === 1n) {
      newSortOrder = newSortOrder.map((index) => index * 2n)
    }

    newSortOrder[idx] = newSortOrder[idx - 1] - 1n

    return newSortOrder
  }
}

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

    this.sortable = Sortable.create(this.targetTarget, {
      onEnd: (event) => {
        const sortIndexInputs = Array.from(
          this.element.querySelectorAll('input[name*=sort_index]')
        )

        const sortOrder = sortIndexInputs.map((el) => BigInt(el.value))
        const newSortOrder = getSortOrder(sortOrder, event.newIndex)

        for (const [idx, el] of sortIndexInputs.entries()) {
          el.value = newSortOrder[idx]
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
