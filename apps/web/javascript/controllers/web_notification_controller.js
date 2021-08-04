import { Controller } from 'stimulus'
import { getApiClient } from 'apps/utils/javascript/api'

export default class extends Controller {
  static targets = ['close'];

  close() {
    this.element.remove();
  }
}
