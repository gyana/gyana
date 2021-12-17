import { Controller } from '@hotwired/stimulus'
import tippy from 'tippy.js'

/**
 * Tippy.js powered interactable popover.
 *
 * @link https://atomiks.github.io/tippyjs/
 *
 * @example
 * <div data-controller="popover">
 *  <button class="button">Click me!</button>
 *
 *  <template data-popover-target="body">
 *    <h1>You can use HTML in popovers</h1>
 *  </template>
 * </div>
 */
export default class extends Controller {
  static targets = ['body', 'trigger']

  connect() {
    console.assert(this.hasBodyTarget, 'Popover controllers need a body target')

    tippy(this.element, {
      allowHTML: true,
      animation: false,
      arrow: false,
      content: this.bodyTarget.innerHTML,
      delay: 0,
      interactive: true,
      appendTo: this.element,
      placement: this.element.dataset.placement || 'bottom',
      theme: this.element.dataset.theme || 'popover',
      trigger: 'click',
      triggerTarget: this.hasTriggerTarget ? this.triggerTarget : this.element,
    })
  }

  disconnect() {
    // https://atomiks.github.io/tippyjs/v6/tippy-instance/#-property
    if (this.element._tippy) {
      this.element._tippy.destroy()
    }
  }
}
