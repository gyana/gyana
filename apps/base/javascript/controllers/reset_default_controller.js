import { Controller } from '@hotwired/stimulus'

/**
 * Controller for form inputs that have a `initial` value, allowing a user to
 * reset to a pre-set default.
 * 
 * @usage
 * <div data-controller="reset-default" data-reset-default-initial-value="2">
 *   <label>My input <a data-reset-default-target="control">Reset to default</a>
 * 
 *   <input type="number"/>
 * </div>
 */
export default class extends Controller {
  static targets = ['control']
  static values = {
    initial: String
  }

  initialize() {
    this.boundHandleClick = this.handleClick.bind(this)
    this.boundHandleChange = this.handleChange.bind(this)
    this.inputElement = this.element.querySelector('input')
  }

  connect() {
    this.inputElement.addEventListener('change', this.boundHandleChange)
    this.controlTarget.addEventListener('click', this.boundHandleClick)

    if (this.inputElement.value != this.initialValue) {
      this.controlTarget.removeAttribute('hidden')
    }
  }

  disconnect() {
    this.inputElement.removeEventListener('change', this.boundHandleChange)
    this.controlTarget.removeEventListener('click', this.boundHandleClick)
  }

  reset() {
    this.element.querySelector('input').value = this.initialValue
  }

  handleClick(event) {
    event.preventDefault()

    this.reset()
    this.controlTarget.setAttribute('hidden', '')
  }

  handleChange(event) {
    if (event.target.value != this.initialValue) {
      this.controlTarget.removeAttribute('hidden')
    }
  }
}
