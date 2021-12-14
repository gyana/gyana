import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ['form']

  updateURL() {
    const data = new FormData(this.formTarget)
    const queryString = new URLSearchParams(data).toString()
    console.log(data)
    history.replaceState({}, '', `${location.pathname}?${queryString}&sumbit=submit`)
  }
}
