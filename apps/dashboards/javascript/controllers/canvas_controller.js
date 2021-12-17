import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['form', 'formControl']

  connect() {
    this.element.ondragover = (event) => {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'move'
    }

    this.element.ondrop = (event) => {
      if (event.dataTransfer.getData('application/gycontrol')) {
        // Default widths is 300
        this.formControlTarget.querySelector('[name=x]').value = event.offsetX - 150
        // Default height is 100
        this.formControlTarget.querySelector('[name=y]').value = event.offsetY - 50
        this.formControlTarget.querySelector('button').disabled = false
        this.formControlTarget.requestSubmit(this.formControlTarget.querySelector('button'))
      } else {
        const data = event.dataTransfer.getData('application/gydashboard')

        // Use a hidden form to create a widget and add to canvas via turbo stream
        console.log(event.offsetX, event.offsetY)
        this.formTarget.querySelector('[name=kind]').value = data
        // Default width is double
        this.formTarget.querySelector('[name=x]').value = event.offsetX - 248
        // Default height is double
        this.formTarget.querySelector('[name=y]').value = event.offsetY - 195
        this.formTarget.querySelector('button').disabled = false

        this.formTarget.requestSubmit(this.formTarget.querySelector('button'))
      }
    }
  }
}
