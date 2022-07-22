import { Controller } from '@hotwired/stimulus'
import CodeMirror from 'codemirror/lib/codemirror.js'
import 'codemirror/addon/mode/simple.js'


/**
 * Facilitates a simple "code-like" input widget.
 */
export default class extends Controller {
  static targets = ['textarea']

  connect() {
    this.CodeMirror = CodeMirror.fromTextArea(this.textareaTarget, {
      lineNumbers: true,
      lineWrapping: true,
    })

    this.CodeMirror.on('blur', function (cm) {
      cm.save()
    })
  }
}
