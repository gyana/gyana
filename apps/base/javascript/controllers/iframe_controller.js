import { Controller } from '@hotwired/stimulus'

// Display placeholder while iframe is loading

export default class extends Controller {
  static targets = ['placeholder']

  connect() {
    this.onIframeLoad = this.onIframeLoad.bind(this)
    this.element.querySelector('iframe').addEventListener('load', this.onIframeLoad)
  }

  disconnect() {
    this.element.querySelector('iframe').removeEventListener('load', this.onIframeLoad)
  }

  onIframeLoad() {
    this.element.querySelector('iframe').style.display = 'block'
    this.placeholderTarget.style.display = 'none'
  }
}
