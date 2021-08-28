import { Controller } from 'stimulus'

/**
 * Simple Tippy.js stimulus wrapper.
 *
 * @link https://atomiks.github.io/tippyjs/
 *
 * @example
 * <p data-controller="tooltip">
 *  Hover over me for a tooltip!
 *  <span data-tooltip-target="body">This is the tooltip!</span>
 * </p>
 */
export default class extends Controller {
  static targets = ['body']

  initialize() {
    tippy.setDefaultProps({
      delay: 0,
      animation: false,
      placement: 'bottom',
    })
  }

  connect() {
    tippy(this.element, {
      content: this.bodyTarget.innerText,
      placement: this.element.dataset.placement,
    })
  }
}
