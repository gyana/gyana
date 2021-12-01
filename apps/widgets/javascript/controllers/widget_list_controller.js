import { Controller } from '@hotwired/stimulus'

/**
 * Adds a focus attribute and changes the z-index when clicking a widget.
 */
export default class extends Controller {
  static targets = ['widget']

  widgetTargetConnected(element) {
    document.addEventListener(
      'mousedown',
      function (event) {
        if (element.contains(event.target)) {
          element.dataset.focused = true
          element.style.zIndex = 1
        } else {
          element.dataset.focused = false
          element.style.zIndex = null
        }
      }.bind(this)
    )
  }
}
