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
 * 
 * @example
 * <p data-controller="tooltip" data-tooltip-content="This is the tooltip!">
 *  Hover over me for a tooltip!
 * </p> 
 */
export default class extends Controller {
  static targets = ['body']

  connect() {
    console.assert(
      this.element.dataset.tooltipContent || this.hasBodyTarget,
      'Tooltip controllers need either a data-tooltip-content attribute or a body target.'
    )

    tippy(this.element, {
      animation: false,
      content: this.hasBodyTarget ? this.bodyTarget.innerText : this.element.dataset.tooltipContent,
      delay: 0,
      // `data-show-on-collapse="true"` on element hides the tooltip when the
      // sidebar is expanded.
      onShow(instance) {
        if (instance.reference.dataset.showOnCollapse && document.querySelector("#sidebar-toggle:checked")) {
          return false
        }
      },
      placement: this.element.dataset.tooltipPlacement || 'bottom',
    })
  }

  disconnect() {
    // https://atomiks.github.io/tippyjs/v6/tippy-instance/#-property
    if (this.element._tippy) {
      this.element._tippy.destroy()
    }
  }
}
