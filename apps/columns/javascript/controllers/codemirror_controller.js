import { Controller } from 'stimulus'
import CodeMirror from 'codemirror/lib/codemirror.js'
import 'codemirror/addon/mode/simple.js'
import 'codemirror/addon/hint/show-hint.js'
import 'codemirror/addon/edit/closebrackets.js'
import 'codemirror/addon/edit/matchbrackets.js'
import 'codemirror/addon/display/placeholder.js'
import 'codemirror/addon/lint/lint.js'

const functions = require('../../functions.json')

// Codemirror editor for formula language with auto-complete, syntax highlighting and linting.

export default class extends Controller {
  static targets = ['textarea']
  connect() {
    const columns = JSON.parse(this.element.querySelector('#columns').innerHTML).map((column) => ({
      text: column,
      loweredText: column.toLowerCase(),
      className: 'text-pink',
    }))

    const readOnly = this.textareaTarget.attributes['readonly'] ? 'nocursor' : false

    registerLinter(columns)

    this.CodeMirror = CodeMirror.fromTextArea(this.textareaTarget, {
      mode: 'gyanaformula',
      hintOptions: {
        hint: autocomplete(columns),
        completeSingle: false,
      },
      autoCloseBrackets: true,
      matchBrackets: true,
      lint: true,
      selfContain: true,
      readOnly,
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

// Syntax highlighting

const operations = functions.map((f) => f.name)
const operationRegex = new RegExp(`\(${operations.join('|')}\)\(?=\\(\)`)
const stringRegex = /"(?:[^\\]|\\.)*?(?:"|$)/
const columnRegex = /[a-zA-Z_][0-9a-zA-Z_]*/g

CodeMirror.defineSimpleMode('gyanaformula', {
  // The start state contains the rules that are initially used
  start: [
    { regex: stringRegex, token: 'string' },
    {
      regex: operationRegex,
      token: 'keyword',
    },
    { regex: columnRegex, token: 'variable' },
    { regex: /TRUE|FALSE/, token: 'atom' },
    { regex: /[0-9]+/i, token: 'number' },
    { regex: /[-+\/*=<>!]+/, token: 'operator' },
  ],
})

// Autocomplete

const operationCompletions = operations.map((op) => ({ text: op, className: 'text-blue' }))

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
    const list = operationCompletions.filter((op) => op.text.startsWith(word)) || []
    list.push(...(columns.filter((column) => column.loweredText.startsWith(word)) || []))
    return {
      list,
      from: CodeMirror.Pos(cursor.line, start),
      to: CodeMirror.Pos(cursor.line, end),
    }
  }
}

// Linter

const incorrectOperationRegex = /([A-Za-z0-9_]*)(?=\()/g

const registerLinter = (columns) =>
  CodeMirror.registerHelper('lint', 'gyanaformula', function (text) {
    const result = []
    const columnNames = columns.map((c) => c.text)

    text.split('\n').forEach((newline, lineIdx) => {
      const operationMatches = [...newline.matchAll(incorrectOperationRegex)]
      operationMatches.forEach((m) => {
        if (m[0] && !(m[0] + '(').match(operationRegex)) {
          result.push({
            message: `Function ${m[0]} does not exist`,
            severity: 'error',
            from: CodeMirror.Pos(lineIdx, m.index),
            to: CodeMirror.Pos(lineIdx, m.index + m[0].length),
          })
        }
      })

      const columnMatches = [...newline.matchAll(columnRegex)]

      columnMatches.forEach((m) => {
        if (
          newline[m.index + m[0].length] != '(' &&
          !columnNames.includes(m[0]) &&
          !(newline[m.index + m[0].length] == '"' && newline[m.index - 1] == '"')
        ) {
          result.push({
            message: `Column ${m[0]} does not exist`,
            severity: 'error',
            from: CodeMirror.Pos(lineIdx, m.index),
            to: CodeMirror.Pos(lineIdx, m.index + m[0].length),
          })
        }
      })
    })

    return result
  })
