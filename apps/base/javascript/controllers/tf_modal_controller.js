import { Controller } from '@hotwired/stimulus'

// Open a modal with the content populated by a turbo-frame
export default class extends Controller {
  static targets = ['modal', 'turboFrame', 'closingWarning', 'form']

  connect() {
    this.changed = false
    const params = new URLSearchParams(window.location.search)

    if (params.get('modal_item') && this.element.getAttribute('data-open-on-param') == '') {
      this.modalTarget.classList.remove('hidden')
    }

    window.addEventListener('keydown', (event) => {
      if (event.key == 'Escape') {
        this.close()
      }
    })

    // Close the modal when clicking outside of the frame
    this.modalTarget.addEventListener('click', (e) => {
      if (!this.turboFrameTarget.contains(e.target)) {
        this.close()
      }
    })
  }

  open(event) {
    this.turboFrameTarget.removeAttribute('src')
    this.turboFrameTarget.innerHTML = `
        <div class='placeholder-scr placeholder-scr--fillscreen'>
          <i class='placeholder-scr__icon fad fa-spinner-third fa-spin fa-2x'></i>
        </div>
      `

    this.turboFrameTarget.setAttribute('src', event.currentTarget.getAttribute('data-src'))

    if (event.currentTarget.getAttribute('data-item')) {
      const params = new URLSearchParams(location.search)
      params.set('modal_item', event.currentTarget.getAttribute('data-item'))
      history.replaceState({}, '', `${location.pathname}?${params.toString()}`)
    }

    this.modalTarget.classList.remove('hidden')
  }

  async submit(e) {
    for (const el of this.formTarget.querySelectorAll('button[type=submit]')) el.disabled = true
    e.target.innerHTML = '<i class="placeholder-scr__icon fad fa-spinner-third fa-spin"></i>'

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

  change() {
    this.changed = true
  }

  close(e) {
    if (this.changed) {
      this.closingWarningTarget.classList.remove('hidden')
    } else {
      if (e.currentTarget.getAttribute('type') == 'submit') {
        this.formTarget.requestSubmit(this.formTarget.querySelector("button[value*='close']"))
      }
      this.forceClose()
    }
  }

  forceClose() {
    this.changed = false
    this.modalTarget.classList.add('hidden')

    const params = new URLSearchParams(location.search)
    params.delete('modal_item')
    history.replaceState(
      {},
      '',
      `${location.pathname}${params.toString() ? '?' + params.toString() : ''}`
    )
  }

  closeWarning() {
    this.closingWarningTarget.classList.add('hidden')
  }

  // Trigger save and preview without clicking save and preview button
  preview() {
    this.changed = false

    setTimeout(() => {
      this.formTarget.requestSubmit(
        this.formTarget.querySelector("button[value*='Save & Preview']")
      )
    }, 0)
  }

  save() {
    this.changed = false
  }
}
