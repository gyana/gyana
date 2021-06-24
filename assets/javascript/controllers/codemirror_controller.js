import { Controller } from 'stimulus'
import CodeMirror from 'codemirror/lib/codemirror.js'
import 'codemirror/addon/mode/simple.js'
import 'codemirror/addon/hint/show-hint.js'

export default class extends Controller {
  static targets = ['textarea']
  connect() {
    const columns = JSON.parse(this.element.querySelector('#columns').innerHTML).map((column) => ({
      text: column,
      loweredText: column.toLowerCase(),
    }))
    this.CodeMirror = CodeMirror.fromTextArea(this.textareaTarget, {
      mode: 'gyanaformula',
      hintOptions: {
        hint: autocomplete(columns),
      },
    })
    // From https://stackoverflow.com/a/54377763
    this.CodeMirror.on('inputRead', function (instance) {
      if (instance.state.completionActive) {
        return
      }
      var cur = instance.getCursor()
      var token = instance.getTokenAt(cur)
      if (token.type && token.type != 'comment') {
        CodeMirror.commands.autocomplete(instance)
      }
    })
  }
}

const operations = [
  'abs',
  'add',
  'between',
  'case',
  'cast',
  'ceil',
  'coalesce',
  'date',
  'day',
  'day_of_week',
  'div',
  'epoch_seconds',
  'exp',
  'find',
  'floor',
  'fillna',
  'hash',
  'hour',
  'ifelse',
  'isnull',
  'join',
  'left',
  'length',
  'like',
  'ln',
  'log',
  'log2',
  'log10',
  'lower',
  'lpad',
  'lstrip',
  'millisecond',
  'minute',
  'month',
  'mul',
  'notnull',
  'pow',
  're_extract',
  're_replace',
  're_search',
  'repeat',
  'rlike',
  'replace',
  'reverse',
  'right',
  'round',
  'rpad',
  'rstrip',
  'second',
  'sqrt',
  'strftime',
  'strip',
  'sub',
  'substitute',
  'substr',
  'time',
  'translate',
  'truncate',
  'upper',
  'year',
]

CodeMirror.defineSimpleMode('gyanaformula', {
  // The start state contains the rules that are initially used
  start: [
    { regex: /"(?:[^\\]|\\.)*?(?:"|$)/, token: 'string' },
    {
      regex: new RegExp(`(?:${operations.join('|')}+)\\(`),
      token: 'keyword',
    },
    { regex: /[a-zA-Z_][0-9a-zA-Z_]*/, token: 'variable' },
    { regex: /TRUE|FALSE/, token: 'atom' },
    { regex: /[0-9]+/i, token: 'number' },
    { regex: /[-+\/*=<>!]+/, token: 'operator' },
  ],
})

const autocomplete = (columns) => (editor, option) => {
  let cursor = editor.getCursor(),
    line = editor.getLine(cursor.line)
  let start = cursor.ch,
    end = cursor.ch
  // get the start of the word
  while (start && /\w/.test(line.charAt(start - 1))) --start
  // get the end of the word
  while (end < line.length && /\w/.test(line.charAt(end))) ++end
  const word = line.slice(start, end).toLowerCase()
  if (word) {
    const list = operations.filter((op) => op.startsWith(word)) || []
    list.push(...(columns.filter((column) => column.loweredText.startsWith(word)) || []))
    return {
      list,
      from: CodeMirror.Pos(cursor.line, start),
      to: CodeMirror.Pos(cursor.line, end),
    }
  }
}
