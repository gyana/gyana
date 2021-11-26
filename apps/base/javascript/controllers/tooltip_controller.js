import { Controller } from '@hotwired/stimulus'
import tippy from 'tippy.js'

/**
 * Simple Tippy.js stimulus wrapper.
 *
 * @link https://atomiks.github.io/tippyjs/
 *
 * @example
 * <p data-controller="tooltip">
 *  Hover over me for a tooltip!
 *  <template data-tooltip-target="body">This is the tooltip!</template>
 * </p>
 */
export default class extends Controller {
  static targets = ['body']

  connect() {
    console.assert(this.hasBodyTarget, 'Tooltip controllers need a body target')

    tippy(this.element, {
      animation: false,
      content: this.bodyTarget.innerText,
      delay: 0,
      placement: this.element.dataset.placement || 'bottom',
    })
  }

  disconnect() {
    // https://atomiks.github.io/tippyjs/v6/tippy-instance/#-property
    if (this.element._tippy) {
      this.element._tippy.destroy()
    }
  }
}
