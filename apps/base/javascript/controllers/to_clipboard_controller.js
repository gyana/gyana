import { Controller } from '@hotwired/stimulus'

/**
 * Copies the text contents of a target element to the users clipboard.
 */
export default class extends Controller {
  static targets = ['target']

  copy() {
    // Inspired by https://stackoverflow.com/questions/36639681/how-to-copy-text-from-a-div-to-clipboard
    if (document.selection) {
      //IE
      const range = document.body.createTextRange()
      range.moveToElementText(this.targetTarget)
      range.select().createTextRange()
      document.execCommand('copy')
      document.getSelection().empty()
    } else {
      // Not IE
      if (navigator.clipboard) {
        navigator.clipboard.writeText(this.targetTarget.innerText.trim())
      } else {
        const range = document.createRange()
        range.selectNode(this.targetTarget)
        window.getSelection().addRange(range)
        console.log(window.getSelection())
        document.execCommand('copy')
        if (window.getSelection().empty) {
          // Chrome
          window.getSelection().empty()
        } else if (window.getSelection().removeAllRanges) {
          // Firefox
          window.getSelection().removeAllRanges()
        }
      }
    }
  }
}
