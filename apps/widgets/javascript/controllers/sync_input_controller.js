import { Controller } from 'stimulus'

export default class extends Controller {
  static values = {
    id: String,
    fieldName: String,
    withDebounce: Boolean,
    apiPath: Array,
    debounceTime: Number,
  }

  update(event) {
    const self = this
    return function () {
      let auth = new coreapi.auth.SessionAuthentication({
        csrfCookieName: 'csrftoken',
        csrfHeaderName: 'X-CSRFToken',
      })

      let client = new coreapi.Client({ auth: auth })

      client.action(window.schema, self.apiPathValue, {
        id: self.idValue,
        [self.fieldNameValue]: event.target.value,
      })
    }
  }

  sync(event) {
    const debounceTime = this.debounceTimeValue || 1000
    if (this.withDebounceValue) {
      if (this.debounce) clearTimeout(this.debounce)
      this.debounce = setTimeout(this.update(event), debounceTime)
    } else {
      this.update(event)()
    }
  }
}
