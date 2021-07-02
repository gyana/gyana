import { Controller } from 'stimulus'

export default class extends Controller {
  static values = {
    inhibitValidate: Boolean,
    taskUrl: String,
    redirectUrl: String,
    scriptUrl: String,
  }

  init() {
    CeleryProgressBar.initProgressBar(this.taskUrlValue, {
      onSuccess: () => {
        this.element.innerHTML = `
          <i class="fas fa-check text-green text-xl mr-4"></i>
          <h4>File successfully validated</h4>
        `

        window.removeEventListener('beforeunload', this.onUnloadCall)
        setTimeout(() => {
          Turbo.visit(this.redirectUrlValue)
        }, 750)
      },
      onError: () => {
        this.element.innerHTML = `
          <i class="fas fa-times text-red text-xl mr-4"></i>
          <h4>Errors occurred when validating your file</h4>
        `
      },
    })
  }

  connect() {
    if (!this.inhibitValidateValue) {
      this.onUnloadCall = (e) => {
        e.preventDefault()
        e.returnValue = ''
      }
      window.addEventListener('beforeunload', this.onUnloadCall)
      if (typeof CeleryProgressBar !== 'undefined') {
        this.init()
      } else {
        var script = document.createElement('script')
        script.src = this.scriptUrlValue
        script.onload = () => window.dispatchEvent(new Event('celeryProgress:load'))
        document.head.appendChild(script)

        // Binding our init function to this, allowing us to access this class' values
        const init = this.init.bind(this)

        window.addEventListener('celeryProgress:load', init, { once: true })
      }
    }
  }

  disconnect() {
    if (!this.inhibitValidateValue) {
      window.removeEventListener('beforeunload', this.onUnloadCall)
    }
  }
}
