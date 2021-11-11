import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ["input"]

  initialize() {
    this.boundHandleDrop = this.handleDrop.bind(this)
    this.boundHandlePaste = this.handlePaste.bind(this)
  }

  connect() {
    // Prevent browser from catching files.
    this.element.addEventListener("dragover", this.handleDragover)
    window.addEventListener("paste", this.boundHandlePaste)
    window.addEventListener("drop", this.boundHandleDrop)
  }

  disconnect() {
    this.element.removeEventListener("dragover", this.handleDragover)
    window.removeEventListener("drop", this.boundHandlePaste)
    window.removeEventListener("drop", this.boundHandleDrop)
  }

  handleDragover(event) {
    event.preventDefault()
  }

  handlePaste(event) {
    const paste = (event.clipboardData || window.clipboardData).getData('text');

    if (event.target.type !== 'text') {
      if (/(.*)?(docs.google.com\/spreadsheets\/)(.*)?/.test(paste)) {
        window.location.href = this.element.dataset.sheetsUrl + '?url=' + encodeURI(paste)
      }
    }
  }

  handleDrop(event) {
    event.preventDefault()

    if (this.hasInputTarget) {
      this.inputTarget.files = event.dataTransfer.files

      // Force GCSFileUpload.tsx to start the upload.
      this.inputTarget.dispatchEvent(new Event('change'))
    }
  }
}
