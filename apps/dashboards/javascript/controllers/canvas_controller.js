import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['form']

  connect() {
    this.element.ondragover = (event) => {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'move'
    }
    this.element.ondrop = (event) => {
      const data = event.dataTransfer.getData('application/gydashboard')
      // Use a hidden form to create a widget and add to canvas via turbo stream
      this.formTarget.querySelector('[name=kind]').value = data
      this.formTarget.querySelector('[name=x]').value = event.offsetX - 248
      this.formTarget.querySelector('[name=y]').value = event.offsetY - 195
      this.formTarget.querySelector('button').disabled = false
      this.formTarget.querySelector('button').click()
    }
  }
}
