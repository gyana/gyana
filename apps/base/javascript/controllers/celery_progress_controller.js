import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = {
    done: Boolean,
    taskUrl: String,
    scriptUrl: String,

    // Either one of these is required. The redirectUrl will trigger a redirect
    // the turboStreamUrl will render a turbo stream on success
    redirectUrl: String,
    turboStreamUrl: String,
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
  }

  async onSuccess() {
    const successTemplate = this.element.querySelector("#success-template")
    if (successTemplate !== null) {
      const successNode = successTemplate.content.cloneNode(true)
      this.element.innerHTML = ""
      this.element.appendChild(successNode)

      window.removeEventListener("beforeunload", this.onUnloadCall)
      if (this.redirectUrlValue) {
        setTimeout(() => {
          Turbo.visit(this.redirectUrlValue)
        }, 750)
      } else if (this.turboStreamUrlValue) {
        const html = await (await fetch(this.turboStreamUrlValue)).text()
        Turbo.renderStreamMessage(html)
      }
    }
  }

  onError(progressBarElement, progressBarMessageElement, excMessage, data) {
    const failureNode = this.element.querySelector("#failure-template").content.cloneNode(true)
    this.element.innerHTML = ""
    this.element.appendChild(failureNode)
    this.element.querySelector('#failure-message').innerHTML = excMessage || ''
  }

  connect() {
    if (!this.dontStartValue) {
      this.element.insertAdjacentHTML(
        "beforeend",
        `<div id="progress-bar" style="display:none;">
          <div id="progress-bar-message"></div>
        </div>`
      )

      window.addEventListener("beforeunload", this.handleBeforeUnload)

      if (typeof CeleryProgressBar !== "undefined") {
        this.init()
      } else {
        var script = document.createElement("script")
        script.src = this.scriptUrlValue
        script.onload = () => window.dispatchEvent(new Event("celeryProgress:load"))
        document.head.appendChild(script)

        // Binding our init function to this, allowing us to access this class" values
        const init = this.init.bind(this)

        window.addEventListener("celeryProgress:load", init, { once: true })
      }
    }
  }

  disconnect() {
    if (!this.dontStartValue) {
      window.removeEventListener("beforeunload", this.onUnloadCall)
    }
  }

  handleBeforeUnload(event) {
    event.preventDefault()
    event.returnValue = ""
  }
}
