import { Controller } from 'stimulus'
import CodeMirror from 'codemirror/lib/codemirror.js'
import 'codemirror/mode/javascript/javascript.js'

export default class extends Controller {
  connect() {
    this.CodeMirror = CodeMirror.fromTextArea(this.element)
  }

  printDoc() {
    console.log('here')
    console.log(this.CodeMirror.getDoc())
  }
}
