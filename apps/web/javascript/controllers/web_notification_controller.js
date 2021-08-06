import { Controller } from 'stimulus'
import { getApiClient } from 'apps/base/javascript/api'

export default class extends Controller {
  static targets = ['close']

  close() {
    this.element.remove()
  }
}
