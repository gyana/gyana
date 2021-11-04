import { Controller } from '@hotwired/stimulus'
import tippy from 'tippy.js';

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
 * </p>
 */
export default class extends Controller {
  static targets = ['body']

  connect() {
    console.assert(this.hasBodyTarget, "Popover controllers need a body target")

    tippy(this.element, {
      allowHTML: true,
      animation: false,
      arrow: false,
      content: this.bodyTarget.innerHTML,
      delay: 0,
      interactive: true,
      placement: this.element.dataset.placement || 'bottom',
      theme: this.element.dataset.theme || 'popover',
      trigger: 'click',
    })
  }

  disconnect() {
    // https://atomiks.github.io/tippyjs/v6/tippy-instance/#-property
    this.element._tippy.destroy()
  }
}
