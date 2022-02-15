import { Controller } from '@hotwired/stimulus'

const debounceTime = 300

/**
 * Modal controller with content populated by a turbo-frame.
 *
 * Pass turbo-frame specific details via data attributes:
 * `data-modal-src`, `data-modal-id`
 *
 * @example
 * <button
 *   data-action="click->tf-modal#open"
 *   data-controller="tooltip"
 *   data-modal-src="{% url "web:help" %}"
 *   data-modal-id="web:help"
 *   data-modal-classes="tf-modal--tall"
 * >
 *  Click me to open a turbo-frame modal!
 * </button>
 */
export default class extends Controller {
  static targets = ['modal', 'turboFrame', 'closingWarning', 'form', 'onParam']

  initialize() {
    this.changed = false
    this.boundHandleKeyup = this.handleKeyup.bind(this)
    this.boundHandleClick = this.handleClick.bind(this)
  }

  connect() {
    window.addEventListener('keyup', this.boundHandleKeyup)
    // Close the modal when clicking outside of the frame
    // TODO: Fix clicking and draging outside of modal closing.
    this.modalTarget.addEventListener('click', this.boundHandleClick)
  }

  disconnect() {
    window.removeEventListener('keyup', this.boundHandleKeyup)
    this.modalTarget.addEventListener('click', this.boundHandleClick)
  }

  onParamTargetConnected(target) {
    const params = new URLSearchParams(window.location.search)

    // We don't want to re-open the modal if a modal is already open.
    if (this.modalTarget.getAttribute('hidden') == null) {
      return
    }

    if (params.get('modal_item')) {
      // This is a little hacky, it simulates a click because we need the
      // data attributes with the turbo-frame src/id.
      this.onParamTarget.click()
    }
  }

  open(event) {
    // Turbo removes the placeholder every time, we need to add it to indicate
    // a loading state.
    this.turboFrameTarget.innerHTML = `
      <div class='placeholder-scr placeholder-scr--fillscreen'>
        <i class='placeholder-scr__icon fad fa-spinner-third fa-spin fa-2x'></i>
      </div>
    `

    this.turboFrameTarget.removeAttribute('src')
    this.turboFrameTarget.setAttribute('id', event.currentTarget.dataset.modalId)
    this.turboFrameTarget.setAttribute('src', event.currentTarget.dataset.modalSrc)

    if (event.currentTarget.dataset.modalTarget) {
      this.turboFrameTarget.setAttribute('target', event.currentTarget.dataset.modalTarget)
    }

    this.modalTarget.className = 'tf-modal'
    if (event.currentTarget.dataset.modalClasses) {
      this.modalTarget.classList.add(...event.currentTarget.dataset.modalClasses.split(' '))
    }

    if (event.currentTarget.dataset.modalItem) {
      const params = new URLSearchParams(location.search)
      params.set('modal_item', event.currentTarget.dataset.modalItem)
      history.replaceState({}, '', `${location.pathname}?${params.toString()}`)
    }

    this.modalTarget.removeAttribute('hidden')
  }

  async submit(e) {
    for (const el of this.formTarget.querySelectorAll('button[type=submit]')) el.disabled = true
    // e.target.innerHTML = '<i class="placeholder-scr__icon fad fa-spinner-third fa-spin"></i>'

    e.preventDefault()
    const data = new FormData(this.formTarget)

    // Live forms need to know that this is a submit request
    // so it know it isnt live anymore
    if (e.target.name) data.set(e.target.name, e.target.value)

    const result = await fetch(this.formTarget.action, {
      method: 'POST',
      body: data,
    })

    const text = await result.text()
    const parser = new DOMParser()
    const doc = parser.parseFromString(text, 'text/html')
    const newForm = doc.querySelector(`#${this.formTarget.id}`)

    this.formTarget.outerHTML = newForm.outerHTML

    if ([200, 201].includes(result.status)) {
      // For nodes, we need to dispatch events
      // that are usually triggered on the default submit event
      const nodeUpdateElement = this.element.querySelector('[data-controller=node-update]')
      if (nodeUpdateElement) {
        this.application
          .getControllerForElementAndIdentifier(nodeUpdateElement, 'node-update')
          .sendNodeEvents()
      }

      this.forceClose()
    }
  }

  change(event) {
    if (event.hasTarget('name') && event.target.getAttribute('name').toLowerCase() != 'search') {
      this.changed = true
    }
  }

  close(event) {
    if (this.hasClosingWarningTarget && this.changed) {
      this.closingWarningTarget.removeAttribute('hidden')
    } else {
      if (this.hasFormTarget && this.formTarget.dataset.tfModalSubmitOnClose != undefined) {
        this.formTarget.requestSubmit(this.formTarget.querySelector("button[value*='close']"))
      }

      this.forceClose()
    }
  }

  forceClose() {
    this.changed = false
    this.modalTarget.setAttribute('hidden', '')

    const params = new URLSearchParams(location.search)
    params.delete('modal_item')
    history.replaceState(
      {},
      '',
      `${location.pathname}${params.toString() ? '?' + params.toString() : ''}`
    )
  }

  closeWarning() {
    this.closingWarningTarget.setAttribute('hidden', '')
  }

  // Trigger save and preview without clicking save and preview button
  preview() {
    this.changed = false

    this.formTarget.requestSubmit(this.formTarget.querySelector("button[value*='Save & Preview']"))
  }

  save() {
    this.changed = false
  }

  search(event) {
    if (this.debounce) clearTimeout(this.debounce)
    this.debounce = setTimeout(this.handleSearch(), debounceTime)
  }

  handleSearch() {
    this.formTarget.requestSubmit(this.formTarget.querySelector("button[value*='close']"))
  }

  handleKeyup(event) {
    if (event.key == 'Escape') {
      this.close(event)
    }
  }

  handleClick(event) {
    if (this.hasTurboFrameTarget && !this.turboFrameTarget.contains(event.target)) {
      this.close(event)
    }
  }
}
