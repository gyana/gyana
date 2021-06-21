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
    { regex: /"(?:[^\\]|\\.)*?(?:"|$)/, token: 'string' },
    {
      regex:
        /(?:abs|add|between|case|cast|ceil|coalesce|date|day|day_of_week|div|epoch_seconds|exp|find|floor|fillna|hash|hour|ifelse|isnull|join|left|length|like|ln|log|log2|log10|lower|lpad|lstrip|millisecond|minute|month|mul|notnull|pow|re_extract|re_replace|re_search|repeat|rlike|replace|reverse|right|round|rpad|rstrip|second|sqrt|strftime|strip|sub|substitute|substr|time|translate|truncate|upper|year+)\(/,
      token: 'keyword',
    },
    { regex: /[a-zA-Z_][0-9a-zA-Z_]*/, token: 'variable' },
    { regex: /TRUE|FALSE/, token: 'atom' },
    { regex: /[0-9]+/i, token: 'number' },
    { regex: /[-+\/*=<>!]+/, token: 'operator' },
  ],
})
