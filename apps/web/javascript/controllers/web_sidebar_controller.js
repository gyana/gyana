import { Controller } from '@hotwired/stimulus'
import { getApiClient } from 'apps/base/javascript/api'

/**
 * Calls the backend API to sync sidebar state with frontend.
 * The sidebar itself uses the `checked` attribute of the input.
 * 
 * See `app_base.html` and `sidebar.scss` for implementation.
 */
export default class extends Controller {
  static targets = ['toggle']

  toggle() {
    getApiClient().action(window.schema, ['toggle-sidebar', 'create'])
  }
}
