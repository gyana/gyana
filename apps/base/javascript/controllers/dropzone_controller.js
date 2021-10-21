import { Controller } from '@hotwired/stimulus'

export default class extends Controller {
  static targets = ["input"]

  connect() {
    // Prevent browser from catching files.
    this.element.addEventListener("dragover", (e) => {
      e.preventDefault()
    })

    this.element.addEventListener("drop", (e) => {
      e.preventDefault()

      this.inputTarget.files = e.dataTransfer.files
      // Force GCSFileUpload.tsx to start the upload.
      this.inputTarget.dispatchEvent(new Event('change'))
    })
  }
}
