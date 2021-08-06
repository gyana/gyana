const EXPECTED_RESPONSE_CODES = [308, 500, 503, 200, 201]

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

  events: [keyof EventMap, EventMap[keyof EventMap]][]

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

    this.shouldChunk = file.size > chunkSize
    this.retryCount = 0

    this.events = []

    if (file.size > maxSize) throw 'This file is too large'
  }

  on<K extends keyof EventMap>(event: K, cb: EventMap[K]) {
    this.events.push([event, cb])
  }
  off(cb: EventMap[keyof EventMap]) {
    const idx = this.events.map(([ev, cb_]) => cb_).indexOf(cb)
    if (idx > -1) {
      this.events.splice(idx, 1)
    }
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

    const end = start + this.chunkSize > this.file.size ? this.file.size : start + this.chunkSize
    const fileChunk = this.shouldChunk ? this.file.slice(start, end) : this.file

    request.upload.addEventListener('progress', (e) => {
      // Get the loaded amount and total filesize (bytes)
      const loaded = start + e.loaded

      // Calculate percent uploaded
      const percentComplete = Math.round((loaded / this.file.size) * 1000) / 10
      this.events.forEach(([ev, cb]) => ev === 'progress' && cb(percentComplete))
    })

    const self = this
    // Load handler when the XHR request returns
    request.addEventListener('load', async () => {
      // 308 Resume Incomplete is returned when chunks are missing
      if (request.status === 308) {
        // Range header can have the following shapes:
        // bytes=0-1999
        // bytes=-2000
        // bytes=2000-
        const newStart = parseInt(
          (request.getResponseHeader('Range') as string).split('-').pop() as string
        )
        // If the start is not NaN we know that there's more to be sent
        if (!Number.isNaN(newStart)) self.sendChunk(newStart)
      }

      if ([500, 503].includes(request.status)) {
        if (self.retryCount < self.maxBackoff) {
          // Our current request has fail so let's retry with an exp backoff
          setTimeout(() => {
            self.retryCount += 1
            self.sendChunk(start)
          }, Math.pow(2, self.retryCount) + Math.ceil(Math.random() * 1000))
        } else {
          // If after the backoff it still fails we throw an error
          this.events.forEach(([ev, cb]) => ev === 'error' && cb())
        }
      }

      if ([200, 201].includes(request.status)) {
        // The upload has completed and succeeded
        this.events.forEach(([ev, cb]) => ev === 'success' && cb())
      }

      // We got an unexpected result, log this in Sentry
      if (!EXPECTED_RESPONSE_CODES.includes(request.status)) {
        this.events.forEach(([ev, cb]) => ev === 'error' && cb())
      }
    })

    request.open('put', this.sessionURI)
    request.responseType = 'blob'
    if (this.shouldChunk) {
      request.setRequestHeader('Content-Range', `bytes ${start}-${end - 1}/${this.file.size}`)
    }
    request.setRequestHeader('x-goog-resumable', 'start')
    request.send(fileChunk)
  }
}

export default GoogleUploader
