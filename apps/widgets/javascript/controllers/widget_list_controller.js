import { Controller } from '@hotwired/stimulus'

/**
 * Adds a focus attribute and changes the z-index when clicking a widget.
 */
export default class extends Controller {
  static targets = ['widget', 'dashboard']

  initialize() {
    this.boundHandleResize = this.handleResize.bind(this)
  }

  connect() {
    if (this.hasDashboardTarget) {
      window.addEventListener('resize', this.boundHandleResize)
      this.boundHandleResize()
    }
  }

  disconnect() {
    window.removeEventListener('resize', this.boundHandleResize)
  }

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

  handleResize(event) {
    const scale = Math.min(
      this.element.clientWidth / parseInt(this.dashboardTarget.style.width)
    );
    this.dashboardTarget.style.transformOrigin = '0 0'
    this.dashboardTarget.style.transform = 'scale(' + scale + ')'
  }
}
