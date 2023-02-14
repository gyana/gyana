import CodeMirror from 'codemirror/lib/codemirror.js'
import 'codemirror/addon/mode/simple.js'

const init = ($el) => {
    const mirror = CodeMirror.fromTextArea(($el), {
      lineNumbers: true,
      lineWrapping: true,
    })
  
    mirror.on('blur', function (cm) {
      cm.save()
    })
}

export const Code = { init }