import { Controller } from '@hotwired/stimulus'
import { getApiClient } from 'apps/base/javascript/api'

const debounceTime = 1000

export default class extends Controller {
  static values = {
    id: String,
    readOnly: { type: Boolean, default: false },
    text: String,
  }

  initialize() {
    this.boundHandleTextChange = this.handleTextChange.bind(this)
  }

  connect() {
    this.quill = new Quill('#editor', {
      placeholder: 'Type your notes here...',
      theme: 'snow',
      readOnly: this.readOnlyValue,
      modules: {
        "toolbar": !this.readOnlyValue
      },
    });

    this.quill.on('text-change', this.boundHandleTextChange);
    this.quill.setContents(JSON.parse(this.textValue))
  }

  disconnect() {
    this.quill.off('text-change', this.boundHandleTextChange);
  }

  update() {
    return () => {
      const client = getApiClient()

      client.action(window.schema, ['widgets', 'api', 'partial_update'], {
        id: this.idValue,
        text_content: JSON.stringify(this.quill.getContents()['ops']),
      })
    }
  }

  handleTextChange(delta, oldDelta, source) {
    if (source == 'user') {
      if (this.debounce) clearTimeout(this.debounce)
      this.debounce = setTimeout(this.update(), debounceTime)
    }
  }
}
