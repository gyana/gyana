interface GoogleUploaderOptions {
  file: File
  target: string
  chunkSize?: number
  maxBackoff?: number
  maxSize?: number
}

interface EventMap {
  progress: (progress: number) => void
  success: () => void
  error: () => void
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

  shouldChunk: boolean
  retryCount: number

  sessionURI: string

  listeners: { [key: keyof EventMap]: EventMap[keyof EventMap][] }

  constructor(options: GoogleUploaderOptions) {
    const {
      file,
      target,
      chunkSize = 10 * 1024 * 1024,
      maxBackoff = 4,
      maxSize = Math.pow(1024, 3),
    } = options
    this.file = file
    this.target = target
    this.chunkSize = chunkSize
    this.maxBackoff = maxBackoff

    this.retryCount = 0

    this.listeners = { progress: [], success: [], error: [] }

    if (file.size > maxSize) throw 'This file is too large'

    this.handleLoad.bind(this)
    this.handleProgress.bind(this)
  }

  addEventListener(event, callback) {
    this.listeners[event].push(callback)
  }
  removeEventListener(event, callback: EventMap[keyof EventMap]) {
    const idx = this.listeners[event].indexOf(callback)
    if (idx > -1) this.listeners[event].splice(idx, 1)
  }

  /**
   * Starts the upload process to GCS.
   *
   * First it initiates the upload by a POST call and then starts sending
   * chunks of the file.
   */
  async start() {
    const sessionResponse = await fetch(this.target, {
      method: 'POST',
      headers: { 'x-goog-resumable': 'start', 'Content-Type': this.file.type },
    })

    this.sessionURI = sessionResponse.headers.get('Location') as string

    if (!this.sessionURI) throw "Couldn't retrieve the session URI"

    this.sendChunk(0)
  }

  /**
   * Recursively send all chunks or whole file to gcs
   *
   * @param start start byte
   */
  sendChunk(start: number) {
    const request = new XMLHttpRequest()

    request.upload.addEventListener('progress', (event) => this.handleProgress(event, start))
    // recursive via handleLoad
    request.addEventListener('load', () => this.handleLoad(request, start))

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
  handleProgress(event: ProgressEvent, start: number) {
    const loaded = start + event.loaded
    const percentComplete = Math.round((loaded / this.file.size) * 1000) / 10
    this.listeners['progress'].forEach((callback) => callback(percentComplete))
  }

  // handle errors, continue with upload or success
  handleLoad(request: XMLHttpRequest, start: number) {
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
        if (!Number.isNaN(newStart)) this.sendChunk(newStart)

      // success
      case 201:
      case 200:
        this.listeners['success'].forEach((callback) => callback())

      // retry failing results with exponential backoff or fail
      case 500:
      case 502:
      case 503:
      case 504:
        if (this.retryCount < this.maxBackoff) {
          setTimeout(() => {
            this.retryCount += 1
            this.sendChunk(start)
          }, Math.pow(2, this.retryCount) + Math.ceil(Math.random() * 1000))
        } else {
          this.listeners['error'].forEach((callback) => callback())
        }

      // unknown error
      default:
        this.listeners['error'].forEach((callback) => callback())
    }
  }
}

export default GoogleUploader
