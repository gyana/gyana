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

    /** @link https://atomiks.github.io/tippyjs/v6/all-props/ */
    tippy(this.element, {
      allowHTML: true,
      animation: false,
      appendTo: this.hasTriggerTarget ? this.element : () => document.body,
      arrow: false,
      content: this.bodyTarget.innerHTML,
      delay: 0,
      interactive: true,
      interactiveBorder: 16,
      maxWidth: 'none',
      placement: this.element.dataset.placement || 'bottom',
      theme: this.element.dataset.theme || 'popover',
      trigger: this.element.dataset.trigger || 'click focus',
      triggerTarget: this.hasTriggerTarget ? this.triggerTarget : this.element,
      zIndex: 'calc(var(--z-ui) + 1)',
      // Tippy dynamically inserts new HTML for the popper
      onShow: (instance) => htmx.process(instance.popper),
    })
  }

  disconnect() {
    // https://atomiks.github.io/tippyjs/v6/tippy-instance/#-property
    if (this.element._tippy) {
      this.element._tippy.destroy()
    }
  }
}
