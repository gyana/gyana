import { Controller } from 'stimulus'

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
      const range = document.createRange()
      range.selectNode(this.targetTarget)
      window.getSelection().addRange(range)
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
