import { Controller } from '@hotwired/stimulus'

const clamp = (value, min, max) => Math.min(Math.max(num, min), max)
const clampToGrid = (value, grid) => Math.ceil(value / grid) * grid

export default class extends Controller {
  static targets = ['form', 'formControl']

  connect() {
    this.element.ondragover = (event) => {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'move'
    }

    this.element.ondrop = (event) => {
      const gridSize = document.querySelector('#dashboard-widget-container').dataset.gridSize

      if (event.dataTransfer.getData('application/gycontrol')) {
        // Default widths is 300
        this.formControlTarget.querySelector('[name=x]').value = clampToGrid(Math.max(event.offsetX - 150, 0), gridSize)
        // Default height is 100
        this.formControlTarget.querySelector('[name=y]').value = clampToGrid(Math.max(event.offsetY - 50, 0), gridSize)
        this.formControlTarget.querySelector('button').disabled = false

        this.formControlTarget.requestSubmit(this.formControlTarget.querySelector('button'))
      } else {
        const data = event.dataTransfer.getData('application/gydashboard')

        if (data && data != '') {
          // Use a hidden form to create a widget and add to canvas via turbo stream
          this.formTarget.querySelector('[name=kind]').value = data
          // Default width is 495, divide by two to get the middle
          this.formTarget.querySelector('[name=x]').value = clampToGrid(Math.max(event.offsetX - 248, 0), gridSize)
          // Default height is 390, divide by two to get the middle
          this.formTarget.querySelector('[name=y]').value = clampToGrid(Math.max(event.offsetY - 195, 0), gridSize)
          this.formTarget.querySelector('button').disabled = false

          this.formTarget.requestSubmit(this.formTarget.querySelector('button'))
        }
      }
    }
  }
}
