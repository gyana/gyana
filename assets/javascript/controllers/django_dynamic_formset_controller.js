import { Controller } from 'stimulus'

// Trigger an event on click

export default class extends Controller {
  static values = {
    selector: String,
  }
  connect() {
    $(function () {
      $('.form-container').formset()
    })
  }
}
