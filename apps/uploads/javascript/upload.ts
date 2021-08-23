interface Listeners {
  onProgress: (progress: number) => void
  onSuccess: () => void
  onError: (error: string) => void
}

interface GoogleUploaderOptions {
  file: File
  target: string
  chunkSize?: number
  maxBackoff?: number
  maxSize?: number
  listeners: Listeners
}

/**
 * Uploader class that specfically works for google resumable uploads.
 *
 * It requires a signed url (`target`) to send a File into GCS from the client. It
 * does so by chunking the files into chunks of max 10MB by default.
 */
class GoogleUploader {
  file: File
  target: string
  chunkSize: number
  maxBackoff: number
  maxSize: number

  shouldChunk: boolean
  retryCount: number

  sessionURI: string
  listeners: Listeners

  constructor(options: GoogleUploaderOptions) {
    const {
      file,
      target,
      listeners,
      chunkSize = window.__cypressChunkSize__ || 10 * 1024 * 1024,
      maxBackoff = window.__cypressMaxBackoff__ || 4,
      maxSize = window.__cypressMaxSize__ || Math.pow(1024, 3),
    } = options
    this.file = file
    this.target = target
    this.listeners = listeners
    this.chunkSize = chunkSize
    this.maxBackoff = maxBackoff
    this.maxSize = maxSize

    this.retryCount = 0

    this._handleLoad.bind(this)
    this._handleProgress.bind(this)
    this._sendChunk.bind(this)
  }

  // start upload with initial POST followed by chunks
  async start() {
    if (this.file.size > this.maxSize) {
      this.listeners.onError('This file is too large')
      return
    }

    const sessionResponse = await fetch(this.target, {
      method: 'POST',
      headers: { 'x-goog-resumable': 'start', 'Content-Type': this.file.type },
    })

    this.sessionURI = sessionResponse.headers.get('Location') as string

    if (!this.sessionURI) throw "Couldn't retrieve the session URI"

    this._sendChunk(0)
  }

  // recursively send all chunks or whole file to gcs
  _sendChunk(start: number) {
    const request = new XMLHttpRequest()

    request.upload.addEventListener('progress', (event) => this._handleProgress(event, start))
    // recursive via _handleLoad
    request.addEventListener('load', () => this._handleLoad(request, start))

    request.open('put', this.sessionURI)
    request.responseType = 'blob'
    request.setRequestHeader('x-goog-resumable', 'start')

    // small files are uploaded directly without chunks
    if (this.file.size > this.chunkSize) {
      const end = Math.min(start + this.chunkSize, this.file.size)
      request.setRequestHeader('Content-Range', `bytes ${start}-${end - 1}/${this.file.size}`)
      request.send(this.file.slice(start, end))
    } else {
      request.send(this.file)
    }
  }

  // get the total loaded and calculate percent uploaded
  _handleProgress(event: ProgressEvent, start: number) {
    const loaded = start + event.loaded
    const percentComplete = Math.round((loaded / this.file.size) * 1000) / 10
    this.listeners.onProgress(percentComplete)
  }

  // handle errors, continue with upload or success
  _handleLoad(request: XMLHttpRequest, start: number) {
    switch (request.status) {
      // chunks are missing
      case 308:
        // Range header can have the following shapes:
        // bytes=0-1999
        // bytes=-2000
        // bytes=2000-
        const newStart = parseInt(
          (request.getResponseHeader('Range') as string).split('-').pop() as string
        )
        // if the start is not NaN we know that there's more to be sent
        if (!Number.isNaN(newStart)) this._sendChunk(newStart)
        return

      // success
      case 201:
      case 200:
        this.listeners.onSuccess()
        return

      // retry failing results with exponential backoff or fail
      case 500:
      case 502:
      case 503:
      case 504:
        if (this.retryCount < this.maxBackoff) {
          setTimeout(() => {
            this.retryCount += 1
            this._sendChunk(start)
          }, Math.pow(2, this.retryCount) + Math.ceil(Math.random() * 1000))
        } else {
          this.listeners.onError('Server error, try again later')
        }
        return

      // unknown error
      default:
        this.listeners.onError('Unknown error')
    }
  }
}

export default GoogleUploader
