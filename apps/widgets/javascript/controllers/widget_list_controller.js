import { Controller } from '@hotwired/stimulus'

/**
 * Adds a focus attribute and changes the z-index when clicking a widget.
 */
export default class extends Controller {
  static targets = ['widget']

  widgetTargetConnected(element) {
    element.addEventListener("mousedown", function () {
      this.focusWidget(element)
    }.bind(this))

    this.focusWidget(element)
  }

  focusWidget(widget) {
    const widgets = this.widgetTargets

    widgets.forEach((widget) => {
      widget.dataset.focused = false
      widget.style.zIndex = null
    })

    widget.dataset.focused = true
    widget.style.zIndex = 1
  }
}
