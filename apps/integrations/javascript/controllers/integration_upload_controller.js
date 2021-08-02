import { Controller } from 'stimulus'
import GoogleUploader from '../upload'
import { getApiClient } from 'apps/utils/javascript/api'

/**
 * Handles resumable uploads directly to GCS using signed urls
 *
 * Using the window javascript object as a state machine. Stimulus
 * controllers tend to reset and re-initialize throughout a user session,
 * the javascript window object stays alive.
 */
export default class extends Controller {
  static values = {
    fileInputId: String,
    fileId: String,
    inhibitUpload: Boolean,
  }

  initialize() {
    if (!window.gyanaFileState) {
      // Prepare the state
      window.gyanaFileState = {}
    }
  }

  /**
   * Main handler for starting a file upload
   *
   * The flow is as follows:
   * 1. Create a signed url in the backend
   * 2. Use this signed url to instantiate the uploader
   * 3. Hook in progress and success callbacks to update UI and trigger the sync on success
   *
   * Note: connect and disconnect are triggered every time the user changes route, we
   * need to carefully manage the registered listeners to avoid multiple callbacks.
   */
  async connect() {
    if (!this.inhibitUploadValue) {
      if (!window.gyanaFileState[this.fileIdValue]) {
        const file = document.getElementById(this.fileInputIdValue).files[0]

        // Now that we got the file we don't need the form anymore.
        document.getElementById('create-form').remove()

        const { url: target } = await getApiClient().action(
          window.schema,
          ['integrations', 'file', 'generate-signed-url', 'create'],
          {
            session_key: this.fileIdValue,
            filename: file.name,
          }
        )

        const uploader = (window.gyanaFileState[this.fileIdValue] = new GoogleUploader({
          target,
          file,
        }))

        uploader.start()
      }

      const self = this
      // https://developer.mozilla.org/en-US/docs/Web/API/WindowEventHandlers/onbeforeunload
      this.onUnloadCall = (e) => {
        e.preventDefault()
        e.returnValue = ''
      }
      this.progressCall = (progress) => {
        self.element.querySelector('#progress').innerHTML = progress + '%'
        self.element.querySelector('#progress-bar').style.strokeDashoffset = 220 - progress * 2.2
      }
      this.successCall = async () => {
        const html = await getApiClient().action(
          window.schema,
          ['integrations', 'file', 'start-sync', 'create'],
          {
            session_key: this.fileIdValue,
          }
        )
        window.removeEventListener('beforeunload', self.onUnloadCall)
        Turbo.renderStreamMessage(html)
      }
      // This unload call spawns a warning when the user tries to unload the page (visiting another url, refreshing the page, etc..)
      window.addEventListener('beforeunload', this.onUnloadCall)
      window.gyanaFileState[this.fileIdValue].on('progress', this.progressCall)
      window.gyanaFileState[this.fileIdValue].on('success', this.successCall)
    }
  }

  disconnect() {
    if (!this.inhibitUploadValue) {
      window.gyanaFileState[this.fileIdValue].off(this.progressCall)
      window.gyanaFileState[this.fileIdValue].off(this.successCall)
      window.removeEventListener('beforeunload', this.onUnloadCall)
    }
  }
}
