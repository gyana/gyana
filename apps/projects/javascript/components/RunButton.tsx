import React, { useState } from 'react'
import Tippy from '@tippyjs/react'
import { runProject } from '../api'

interface Props {
  projectId: number
  setRunInfo: React.Dispatch<React.SetStateAction<{ [key in string]: string }>>
}

const RunButton: React.FC<Props> = ({ projectId, setRunInfo }) => {
  const [loading, setLoading] = useState(false)

  const initCeleryProgress = (taskId: string) => {
    CeleryProgressBar.initProgressBar(`/celery-progress/${taskId}`, {
      onSuccess: async (_, __, result) => {
        setLoading(false)
        setRunInfo((runInfo) => ({ ...runInfo, project: 'success' }))
        alert('Project finished running!')
      },
      onError: (_, __, excMessage) => {
        setLoading(false)
        setRunInfo((runInfo) => ({ ...runInfo, project: 'failed' }))
        alert(`Project failed running: ${excMessage}`)
      },
      onProgress: (_, __, progress) => {
        if (progress.description) {
          setRunInfo(JSON.parse(progress.description))
        }
      },
      // override the defaults, otherwise they will raise errors
      onRetry: () => { },
    })
  }

  return (
    <Tippy content='Run all your integrations and workflows in order'>
      <div className='dndflow__run-button'>
        <button
          data-cy='project-run'
          onClick={async () => {
            setLoading(true)
            const result = await runProject(projectId)
            initCeleryProgress(result.task_id)
          }}
          className='button button--sm button--success'
          disabled={loading}
        >
          {loading ? (
            <i className='fad fa-fw fa-spinner-third fa-spin' />
          ) : (
            <i className='fas fa-fw fa-play'></i>
          )}
          Run all
        </button>
      </div>
    </Tippy>
  )
}

export default RunButton
