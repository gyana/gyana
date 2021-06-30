import { Controller } from 'stimulus'

export default class extends Controller {
  static values = {
    taskUrl: String,
    scriptUrl: String,
  }

  /**
   * Handles loading of the progress script if not defined, making it a self-contained component
   *
   * Checks for CeleryProgressBar to be in global scope, if not we first load the script which
   * onload runs our init call.
   */
  connect() {
    this.element.querySelector('.progress-success').style = 'display: none;'
    this.element.querySelector('.progress-inprogress').style = 'display: none;'

    if (typeof CeleryProgressBar !== 'undefined') {
      this.initProgressBar()
    } else {
      var script = document.createElement('script')
      script.src = this.scriptUrlValue
      script.onload = () => window.dispatchEvent(new Event('celeryProgress:load'))
      document.head.appendChild(script)

      // Binding our init function to this, allowing us to access this class' values
      const init = this.initProgressBar.bind(this)

      window.addEventListener('celeryProgress:load', init, { once: true })
    }
  }

  initProgressBar() {
    // Binding the methods to `this` so we can access this controllers attributes
    const onProgress = this.onProgress.bind(this)
    const onSuccess = this.onSuccess.bind(this)
    CeleryProgressBar.initProgressBar(this.taskUrlValue, {
      onProgress: onProgress,
      onSuccess: onSuccess,
    })
  }

  onProgress(progressBarElement, progressBarMessageElement, progress) {
    this.element.querySelector('.progress-inprogress').style = 'display: initial;'

    progressBarElement.style.backgroundColor = '#68a9ef'
    progressBarElement.style.width = progress.percent + '%'

    if (progress.current == 0) {
      if (progress.pending === true) {
        progressBarMessageElement.textContent = 'Waiting for sync to start...'
      } else {
        progressBarMessageElement.textContent = 'Sync started...'
      }
    } else {
      progressBarMessageElement.textContent =
        progress.current + ' of ' + progress.total + ' tasks processed. '
    }
  }

  onSuccess(progressBarElement, progressBarMessageElement, result) {
    this.element.querySelector('.progress-inprogress').style = 'display: none;'
    this.element.querySelector('.progress-success').style = 'display: initial;'

    progressBarElement.style.backgroundColor = '#76ce60'
    progressBarMessageElement.textContent = '✅ Sync successfully completed!'
  }
}
