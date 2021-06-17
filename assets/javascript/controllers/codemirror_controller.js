import { Controller } from 'stimulus'
import CodeMirror from 'codemirror/lib/codemirror.js'
import 'codemirror/addon/mode/simple.js'

export default class extends Controller {
  connect() {
    this.CodeMirror = CodeMirror.fromTextArea(this.element, { mode: 'simplemode' })
  }
}

CodeMirror.defineSimpleMode('simplemode', {
  // The start state contains the rules that are initially used
  start: [
    // The regex matches the token, the token property contains the type
    { regex: /"(?:[^\\]|\\.)*?(?:"|$)/, token: 'string' },

    // { regex: /(function)(\s+)([a-z$][\w$]*)/, token: ['keyword', null, 'variable-2'] },

    { regex: /(?:[a-zA-Z]+)\b\(.*\)/, token: 'keyword' },
    { regex: /[a-zA-Z_][0-9a-zA-Z_]*/, token: 'variable' },
    { regex: /TRUE|FALSE/, token: 'atom' },
    { regex: /[0-9]+/i, token: 'number' },
    // { regex: /\/\/.*/, token: 'comment' },
    // { regex: /\/(?:[^\\]|\\.)*?\//, token: 'variable-3' },
    // // A next property will cause the mode to move to a different state
    // { regex: /\/\*/, token: 'comment', next: 'comment' },
    { regex: /[-+\/*=<>!]+/, token: 'operator' },
    // // indent and dedent properties guide autoindentation
    // { regex: /[\{\[\(]/, indent: true },
    // { regex: /[\}\]\)]/, dedent: true },
  ],
})
