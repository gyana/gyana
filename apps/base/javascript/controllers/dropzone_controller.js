import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ["input"]

  connect() {
    // Prevent browser from catching files.
    this.element.addEventListener("dragover", (e) => {
      e.preventDefault()
    })

    window.addEventListener("paste", (e) => {
      const paste = (e.clipboardData || window.clipboardData).getData('text');

      if (e.target.type !== 'text') {
        if (/(.*)?(docs.google.com\/spreadsheets\/)(.*)?/.test(paste)) {
          window.location.href = this.element.dataset.sheetsUrl + '?url=' + encodeURI(paste)
        }
      }
    })

    window.addEventListener("drop", (e) => {
      e.preventDefault()

      if (e.target.type !== 'text') {
        if (/(.*)?(docs.google.com\/spreadsheets\/)(.*)?/.test(e.dataTransfer.getData("text"))) {
          window.location.href = this.element.dataset.sheetsUrl + '?url=' + encodeURI(e.dataTransfer.getData("text"))
        }
      }

      if (this.hasInputTarget) {
        this.inputTarget.files = e.dataTransfer.files
        // Force GCSFileUpload.tsx to start the upload.
        this.inputTarget.dispatchEvent(new Event('change'))
      }
    })
  }
}
