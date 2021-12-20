import { Controller } from '@hotwired/stimulus'

// Open a modal with the content populated by a turbo-frame
export default class extends Controller {
  static targets = ['modal', 'turboFrame', 'closingWarning', 'form', 'onParam']

  connect() {
    this.changed = false

    window.addEventListener('keyup', (event) => {
      if (event.key == 'Escape') {
        this.close(event)
      }
    })

    // Close the modal when clicking outside of the frame
    // TODO: Fix clicking and draging outside of modal closing.
    this.modalTarget.addEventListener('click', (event) => {
      if (!this.turboFrameTarget.contains(event.target)) {
        this.close(event)
      }
    })
  }

  onParamTargetConnected(target) {
    const params = new URLSearchParams(window.location.search)

    if (params.get('modal_item')) {
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
    this.modalTarget.className = "tf-modal"

    if (event.currentTarget.dataset.modalTarget) {
      this.turboFrameTarget.setAttribute('target', event.currentTarget.dataset.modalTarget)
    }

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
    if (this.hasClosingWarningTarget && this.changed) {
      this.closingWarningTarget.removeAttribute('hidden')
    } else {
      if (e.currentTarget.getAttribute && e.currentTarget.getAttribute('type') == 'submit') {
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
