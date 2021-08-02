import { Controller } from 'stimulus'
import { getApiClient } from 'apps/utils/javascript/api'

const debounceTime = 1000

export default class extends Controller {
  static values = {
    id: String,
  }

  update(event) {
    return () => {
      const client = getApiClient()

      client.action(window.schema, ['widgets', 'api', 'partial_update'], {
        id: this.idValue,
        text_content: event.target.value,
      })
    }
  }

  connect() {
    this.element.addEventListener('input', (event) => {
      if (this.debounce) clearTimeout(this.debounce)
      this.debounce = setTimeout(this.update(event), debounceTime)
    })
  }
}
