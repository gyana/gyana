import { Controller } from '@hotwired/stimulus'
import { getApiClient } from 'apps/base/javascript/api'

export default class extends Controller {
  static targets = ['toggle']

  toggle() {
    getApiClient().action(window.schema, ['toggle-sidebar', 'create'])
  }
}
