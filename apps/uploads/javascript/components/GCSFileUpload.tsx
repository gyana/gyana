import { getApiClient } from 'apps/base/javascript/api'
import React, { useEffect, useRef, useState } from 'react'
import ReactDOM from 'react-dom'
import GoogleUploader from '../upload'

interface IProps {
  name: string
  accept: string
}

type Stage = 'initial' | 'progress' | 'done' | 'error'

const start_upload = async (input: HTMLInputElement, setProgress, setStage, inputRef) => {
  setStage('progress')

  const file = input.files[0]

  const { url: target, path } = await getApiClient().action(
    window.schema,
    ['uploads', 'file', 'generate-signed-url', 'create'],
    {
      // session_key: this.fileIdValue,
      filename: file.name,
    }
  )

  inputRef.current.value = path

  const uploader = new GoogleUploader({
    target,
    file,
  })

  uploader.start()

  uploader.addEventListener('progress', (p) => setProgress(p))
  uploader.addEventListener('success', () => setStage('success'))
}

const GCSFileUpload_: React.FC<IProps> = ({ name, accept }) => {
  const fileRef = useRef<HTMLInputElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const [progress, setProgress] = useState(0)
  // const uploader = useRef<GoogleUploader | null>(null)
  const [stage, setStage] = useState<Stage>('initial')

  useEffect(() => {
    if (fileRef.current) {
      fileRef.current.addEventListener('change', (event) => {
        start_upload(event.target, setProgress, setStage, inputRef)
      })
    }
  }, [])

  return (
    <>
      <input ref={inputRef} type='hidden' id={`id_${name}`} name={name} />
      <ul className='integration__create-flow'>
        <li>
          <div className='integration__file-upload'>
            {stage === 'initial' ? (
              <input ref={fileRef} type='file' accept={accept} />
            ) : stage === 'progress' ? (
              <>
                <div className='integration__file-progress mr-4'>
                  <svg height='80' width='80' style={{ strokeDashoffset: 220 - progress * 2.2 }}>
                    <circle cx='40' cy='40' r='35' strokeWidth='3' fill='transparent' />
                  </svg>
                  <h4>{progress}%</h4>
                </div>
                <div>
                  <h1>Uploading your file...</h1>
                  <p>Uploading the file might take a while, make sure to stay on the page.</p>
                </div>
              </>
            ) : (
              <>
                <i className='fas fa-check text-green text-xl mr-4'></i>
                <div>
                  <h4>File uploaded</h4>
                </div>
              </>
            )}
          </div>
        </li>
      </ul>
    </>
  )
}

class GCSFileUpload extends HTMLElement {
  connectedCallback() {
    console.assert(!!this.parentElement, 'gcs-file-upload requires a container element')

    const name = this.attributes['name'].value
    const accept = this.attributes['accept'].value

    ReactDOM.render(<GCSFileUpload_ name={name} accept={accept} />, this)
  }
}

export default GCSFileUpload
