import { getApiClient } from 'apps/base/javascript/api'
import React, { useEffect, useRef, useState } from 'react'
import ReactDOM from 'react-dom'
import GoogleUploader from '../upload'

interface IProps {
  name: string
}

type Stage = 'initial' | 'progress' | 'done' | 'error'

const GCSFileUpload_: React.FC<IProps> = ({ name }) => {
  const fileRef = useRef<HTMLInputElement>(null)
  const inputFileRef = useRef<HTMLInputElement>(null)
  const inputNameRef = useRef<HTMLInputElement>(null)
  const [progress, setProgress] = useState(0)
  const [stage, setStage] = useState<Stage>('initial')
  const [error, setError] = useState<string>()

  useEffect(() => {
    if (fileRef.current && inputFileRef.current && inputNameRef.current) {
      fileRef.current.addEventListener('change', async (event) => {
        setStage('progress')

        const file = event.target.files[0]

        const { url: target, path } = await getApiClient().action(
          window.schema,
          ['uploads', 'file', 'generate-signed-url', 'create'],
          {
            filename: file.name,
          }
        )

        const uploader = new GoogleUploader({
          target,
          file,
          listeners: {
            onProgress: setProgress,
            onSuccess: () => {
              setStage('done')
              inputFileRef.current.value = path
              inputNameRef.current.value = file.name

              inputFileRef.current.closest('form').submit()
            },
            onError: (error) => {
              setError(error)
              setStage('error')
            },
          },
        })

        uploader.start()
      })
    }
  }, [])

  return (
    <>
      {/* pass the file_name to django as well */}
      <input ref={inputNameRef} type='hidden' id={`id_name`} name='file_name' />
      <input ref={inputFileRef} type='hidden' id={`id_${name}`} name={name} />
      <ul className='integration__create-flow'>
        <li>
          <div className='integration__file-upload'>
            {stage === 'initial' ? (
              <input ref={fileRef} type='file' accept='.csv' />
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
            ) : stage === 'done' ? (
              <>
                <i className='fas fa-check text-green text-xl mr-4'></i>
                <div>
                  <h4>File uploaded</h4>
                </div>
              </>
            ) : (
              <>
                <i className='fas fa-times text-red text-xl mr-4'></i>
                <div className='flex flex-col'>
                  <h4>Errors occurred when uploading your file</h4>
                  <p>{error}</p>
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

    ReactDOM.render(<GCSFileUpload_ name={name} />, this)
  }
}

export default GCSFileUpload
