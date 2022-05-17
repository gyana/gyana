import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['form', 'formControl']

  connect() {
    this.element.ondragover = (event) => {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'move'
    }

    this.element.ondrop = (event) => {
      // Get offset relative to canvas, not drop target (which could be any widget).
      const {top, left} = this.element.getBoundingClientRect()
      const offsetX = Math.round(event.clientX - left)
      const offsetY = Math.round(event.clientY - top)

      if (event.dataTransfer.getData('application/gycontrol')) {
        // Default widths is 300
        this.formControlTarget.elements['x'].value = offsetX - 150
        // Default height is 100
        this.formControlTarget.elements['y'].value = offsetY - 50
        this.formControlTarget.elements['submit'].disabled = false

        this.formControlTarget.requestSubmit(this.formControlTarget.elements['submit'])
      } else {
        const data = event.dataTransfer.getData('application/gydashboard')

        if (data && data != '') {
          // Use a hidden form to create a widget and add to canvas via turbo stream
          this.formTarget.elements['kind'].value = data
          // Default width is 495, divide by two to get the middle
          this.formTarget.elements['x'].value = offsetX - 248
          // Default height is 390, divide by two to get the middle
          this.formTarget.elements['y'].value = offsetY - 195
          this.formTarget.elements['submit'].disabled = false

          this.formTarget.requestSubmit(this.formTarget.elements['submit'])
        }
      }
    }
  }
}
