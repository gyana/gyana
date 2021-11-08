import { Controller } from '@hotwired/stimulus'

// Clicking a widget brings it to the foreground using z-index

export default class extends Controller {
  static targets = ['widget']

  register(event) {
    const widgets = this.widgetTargets

    widgets.forEach((target) => {
      target.onmousedown = function () {
        widgets.forEach((widget) => {
          widget.dataset.focused = false
          widget.style.zIndex = null
        })

        target.dataset.focused = true
        target.style.zIndex = 1
      }
    })

    // When event is defined it means this function is called from a DOM element
    // which then means that we need to register a new widget. To make sure
    // we keep the overlap consistent for this new element we manually set
    // the zindex for the closest widget target
    if (event) {
      const closest = event.target.closest('[data-widget-list-target="widget"]')
      widgets.forEach((widget) => {
        widget.style.zIndex = null
      })
      closest.style.zIndex = 1
    }
  }

  connect() {
    this.register()
  }
}
