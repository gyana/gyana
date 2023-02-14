import { Controller } from '@hotwired/stimulus'

/**
 * Hooks CeleryProgress to a backend task and updates accordingly.
 */
export default class extends Controller {
  static values = {
    done: Boolean,
    taskUrl: String,
    scriptUrl: String,
    redirectUrl: String,
  }

  init() {
    if (this.doneValue) {
      this.onSuccess()
      return
    }

    CeleryProgressBar.initProgressBar(this.taskUrlValue, {
      onSuccess: this.onSuccess.bind(this),
      onError: this.onError.bind(this),
    })
    this.initialURL = window.location.href
  }

  async onSuccess() {
    /**
     * If the user has navigated away from the page the task started on, we
     * don't want to forcibly navigate them away.
     */
    if (this.initialURL != window.location.href) {
      return
    }

    const successTemplate = this.element.querySelector('#success-template')
    if (successTemplate !== null) {
      const successNode = successTemplate.content.cloneNode(true)
      this.element.innerHTML = ''
      this.element.appendChild(successNode)

      window.removeEventListener('beforeunload', this.onUnloadCall)
      setTimeout(() => {
        htmx.ajax('GET', this.redirectUrlValue, 'body')
      }, 750)
    }
  }

  onError(progressBarElement, progressBarMessageElement, excMessage, data) {
    const failureNode = this.element
      .querySelector('#failure-template')
      .content.cloneNode(true)
    this.element.innerHTML = ''
    this.element.appendChild(failureNode)
    this.element.querySelector('#failure-message').innerHTML = excMessage || ''
  }

  connect() {
    if (!this.dontStartValue) {
      this.element.insertAdjacentHTML(
        'beforeend',
        `<div id="progress-bar" style="display:none;">
          <div id="progress-bar-message"></div>
        </div>`
      )

      window.addEventListener('beforeunload', this.handleBeforeUnload)

      if (typeof CeleryProgressBar !== 'undefined') {
        this.init()
      } else {
        var script = document.createElement('script')
        script.src = this.scriptUrlValue
        script.onload = () =>
          window.dispatchEvent(new Event('celeryProgress:load'))
        document.head.appendChild(script)

        // Binding our init function to this, allowing us to access this class" values
        const init = this.init.bind(this)

        window.addEventListener('celeryProgress:load', init, { once: true })
      }
    }
  }

  disconnect() {
    if (!this.dontStartValue) {
      window.removeEventListener('beforeunload', this.handleBeforeUnload)
    }
  }

  handleBeforeUnload(event) {
    event.preventDefault()
    event.returnValue = ''
  }
}
