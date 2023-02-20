import { getApiClient } from 'apps/base/javascript/api'
import React, { useCallback, useEffect, useRef, useState } from 'react'
import ReactDOM from 'react-dom'
import GoogleUploader from '../upload'

interface IProps {
  name: string
  value?: string
}

type Stage = 'initial' | 'progress' | 'done' | 'error'

function handleBeforeUnload(event) {
  // Preventing default in Firefox will always show pop-up
  event.preventDefault()
  // Chrome requires returnValue to be set to show pop-up
  event.returnValue = ''
}

const GCSFileUpload_: React.FC<IProps> = ({ name, value }) => {
  const fileRef = useRef<HTMLInputElement>(null)
  const inputFileRef = useRef<HTMLInputElement>(null)
  const inputNameRef = useRef<HTMLInputElement>(null)
  const [progress, setProgress] = useState(0)
  const [stage, setStage] = useState<Stage>('initial')
  const [error, setError] = useState<string>()

  // prevent browser from catching files.
  const handleDragover = useCallback((event) => event.preventDefault(), [])

  const handleDrop = useCallback((event) => {
    event.preventDefault()

    if (fileRef.current) {
      fileRef.current.files = event.dataTransfer.files

      // trigger the upload
      fileRef.current.dispatchEvent(new Event('change'))
    }
  }, [])

  useEffect(() => {
    document.addEventListener('dragover', handleDragover)
    window.addEventListener('drop', handleDrop)
    return () => {
      document.removeEventListener('dragover', handleDragover)
      window.removeEventListener('drop', handleDrop)
    }
  }, [])

  useEffect(() => {
    if (fileRef.current && inputFileRef.current && inputNameRef.current) {
      fileRef.current.addEventListener('change', async (event) => {
        window.addEventListener('beforeunload', handleBeforeUnload)
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
            onProgress: (progress) => {
              setProgress(progress)
            },
            onSuccess: () => {
              window.removeEventListener('beforeunload', handleBeforeUnload)

              setStage('done')

              inputFileRef.current.value = path
              inputNameRef.current.value = file.name

              !value && inputFileRef.current.closest('form').submit()
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
      <input ref={inputNameRef} type='hidden' id='id_name' name='file_name' />
      <input
        ref={inputFileRef}
        type='hidden'
        id={`id_${name}`}
        name={name}
        value={value}
      />
      <ul className='integration__create-flow'>
        <li>
          <div className='integration__file-upload'>
            {stage === 'initial' ? (
              <div className='flex flex-col'>
                {!value && (
                  <>
                    <h2>Drag and drop a file here</h2>

                    <p className='text-black-50 text-center my-3'>or</p>
                  </>
                )}
                <label
                  className='button button--success button--outline'
                  htmlFor='gcsfileupload'
                >
                  Choose a file to upload
                </label>
                <input
                  data-dropzone-target='input'
                  id='gcsfileupload'
                  ref={fileRef}
                  type='file'
                  accept='.csv'
                  hidden
                />
              </div>
            ) : stage === 'progress' ? (
              <div className='flex flex-col'>
                <div className='integration__file-progress mr-4'>
                  <svg
                    height='120'
                    width='120'
                    style={{ strokeDashoffset: 220 - progress * 2.2 }}
                  >
                    <circle
                      cx='60'
                      cy='60'
                      r='35'
                      strokeWidth='3'
                      fill='transparent'
                    />
                  </svg>
                  <h4>{progress}%</h4>
                </div>
                <p>This might take a few minutes, stay on the page.</p>
              </div>
            ) : stage === 'done' ? (
              <>
                <i className='fas fa-fw fa-4x fa-check text-green'></i>
                <h4>File uploaded</h4>
                {!value && <p>You'll be redirected shortly</p>}
              </>
            ) : (
              <>
                <i className='fas fa-fw fa-4x fa-times text-red'></i>
                <h4>Errors occurred when uploading your file</h4>
                <p>{error}</p>
                <a
                  onClick={() => setStage('initial')}
                  className='button button--tertiary cursor-pointer'
                >
                  Go back
                </a>
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
    console.assert(
      !!this.parentElement,
      'gcs-file-upload requires a container element'
    )

    const name = this.attributes['name'].value
    let value = this.attributes['value'].value
    value = value != 'None' ? value : undefined

    ReactDOM.render(<GCSFileUpload_ name={name} value={value} />, this)
  }
}

export default GCSFileUpload
