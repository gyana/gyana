import { Controller } from '@hotwired/stimulus'

/**
 * Controller that helps mock a radio select using a list of
 * table IDs.
 * 
 * See `input_node.html` for usage example.
 */
export default class extends Controller {
  static targets = ['input', 'label']

  select(event) {
    this.inputTarget.value = event.currentTarget.id

    // Remove css from previous selected target
    this.labelTargets.forEach((label) => {
      label.classList.remove('checkbox--checked')
    })

    // Add css to now selected element
    event.currentTarget.classList.add('checkbox--checked')
  }
}
