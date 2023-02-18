import { Controller } from '@hotwired/stimulus'

const debounceTime = 450

/**
 * Modal controller with content populated by a htmx request.
 *
 * Pass htmx specific details via data attributes:
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
 *  Click me to open a htmx modal!
 * </button>
 */
export default class extends Controller {
  static targets = ['modal', 'htmx', 'closingWarning', 'form', 'onParam']

  initialize() {
    this.changed = false
    this.changeElement = null
    this.boundHandleKeyup = this.handleKeyup.bind(this)
    this.boundHandleClick = this.handleClick.bind(this)
    this.forceClose = this.forceClose.bind(this)
  }

  connect() {
    window.addEventListener('keyup', this.boundHandleKeyup)
    // Close the modal when clicking outside of the frame
    // TODO: Fix clicking and draging outside of modal closing.
    this.modalTarget.addEventListener('click', this.boundHandleClick)
    window.addEventListener('closeModal', this.forceClose)
  }

  disconnect() {
    window.removeEventListener('keyup', this.boundHandleKeyup)
    this.modalTarget.addEventListener('click', this.boundHandleClick)
    window.removeEventListener('closeModal', this.forceClose)
  }

  onParamTargetConnected(target) {
    const params = new URLSearchParams(window.location.search)

    // We don't want to re-open the modal if a modal is already open.
    if (this.modalTarget.getAttribute('hidden') == null) {
      return
    }

    if (params.get('modal_item')) {
      // This is a little hacky, it simulates a click because we need the
      // data attributes with the htmx src.
      this.onParamTarget.click()
    }
  }

  open(event) {
    // HTMX removes the placeholder every time, we need to add it to indicate
    // a loading state.
    this.htmxTarget.innerHTML = `
      <div class='placeholder-scr placeholder-scr--fillscreen'>
        <i class='placeholder-scr__icon fad fa-spinner-third fa-spin fa-2x'></i>
      </div>
    `

    this.htmxTarget.setAttribute('hx-get', event.currentTarget.dataset.modalSrc)

    if (event.currentTarget.dataset.modalTarget) {
      this.htmxTarget.setAttribute(
        'target',
        event.currentTarget.dataset.modalTarget
      )
    }

    this.modalTarget.className = 'tf-modal'
    if (event.currentTarget.dataset.modalClasses) {
      this.modalTarget.classList.add(
        ...event.currentTarget.dataset.modalClasses.split(' ')
      )
    }

    if (event.currentTarget.dataset.modalItem) {
      const params = new URLSearchParams(location.search)
      params.set('modal_item', event.currentTarget.dataset.modalItem)
      history.replaceState({}, '', `${location.pathname}?${params.toString()}`)
    }

    this.modalTarget.removeAttribute('hidden')

    htmx.process(this.htmxTarget)
    this.htmxTarget.dispatchEvent(new CustomEvent('hx-modal-load'))
  }

  async submit(e) {
    for (const el of this.formTarget.querySelectorAll('button[type=submit]'))
      el.disabled = true
    // e.target.innerHTML = '<i class="placeholder-scr__icon fad fa-spinner-third fa-spin"></i>'

    e.preventDefault()
    const data = new FormData(this.formTarget)

    // Live forms need to know that this is a submit request
    // so it know it isnt live anymore
    if (e.target.name) data.set(e.target.name, e.target.value)

    const result = await fetch(
      this.formTarget.getAttribute('hx-post') || this.formTarget.action,
      {
        method: 'POST',
        body: data,
      }
    )

    const text = await result.text()
    const parser = new DOMParser()
    const doc = parser.parseFromString(text, 'text/html')
    const newForm = doc.querySelector(`#${this.formTarget.id}`)

    if (newForm) {
      this.formTarget.outerHTML = newForm.outerHTML
    }

    if ([200, 201].includes(result.status)) {
      // For nodes, we need to dispatch events
      // that are usually triggered on the default submit event

      // const nodeUpdateElement = this.element.querySelector(
      //   '[data-controller=node-update]'
      // )
      // if (nodeUpdateElement) {
      //   this.application
      //     .getControllerForElementAndIdentifier(
      //       nodeUpdateElement,
      //       'node-update'
      //     )
      //     .sendNodeEvents()
      // }

      // Fix this

      const nodeUpdateElement = this.element.querySelector('#node-update-form')

      if (nodeUpdateElement) {
        window.dispatchEvent(new Event('submit'))
      }

      this.forceClose()
    }
  }

  change(event) {
    if (
      event.target.hasAttribute('name') &&
      event.target.getAttribute('name').toLowerCase() != 'search'
    ) {
      this.changed = true
    }
  }

  changeTab(event) {
    if (this.changed) {
      event.preventDefault()
      this.changeElement = event.target
      this.closingWarningTarget.removeAttribute('hidden')
    }
  }

  close(event) {
    if (this.hasClosingWarningTarget && this.changed) {
      this.closingWarningTarget.removeAttribute('hidden')
    } else {
      if (
        this.hasFormTarget &&
        this.formTarget.dataset.tfModalSubmitOnClose != undefined
      ) {
        this.formTarget.requestSubmit(
          this.formTarget.querySelector("button[value*='close']")
        )
      }

      this.forceClose()
    }
  }

  forceClose() {
    this.changed = false

    if (this.changeElement) {
      const element = this.changeElement
      this.changeElement = null
      element.click()
    } else {
      this.modalTarget.setAttribute('hidden', '')

      const params = new URLSearchParams(location.search)
      params.delete('modal_item')
      history.replaceState(
        {},
        '',
        `${location.pathname}${
          params.toString() ? '?' + params.toString() : ''
        }`
      )
    }
  }

  closeWarning() {
    this.closingWarningTarget.setAttribute('hidden', '')
  }

  // Trigger save and preview without clicking save and preview button
  preview(e) {
    e.preventDefault()
    this.changed = false
    this.formTarget.requestSubmit(
      this.formTarget.querySelector("button[value*='Save & Preview']")
    )
  }

  save(e) {
    this.changed = false

    if (
      e.detail &&
      e.detail.success &&
      e.detail.formSubmission.submitter.value == 'Save & Close'
    ) {
      this.forceClose()
    }
  }

  search(event) {
    if (this.debounce) clearTimeout(this.debounce)
    this.debounce = setTimeout(
      this.handleSearch.bind(this, event),
      debounceTime
    )
  }

  handleSearch(event) {
    this.liveUpdateController.updateForm(event)
  }

  handleKeyup(event) {
    if (event.key == 'Escape') {
      this.close(event)
    }
  }

  handleClick(event) {
    if (this.hashtmxTarget && !this.htmxTarget.contains(event.target)) {
      this.close(event)
    }
  }

  get liveUpdateController() {
    return this.application.getControllerForElementAndIdentifier(
      this.formTarget,
      'live-update'
    )
  }
}
