import { isNode } from 'react-flow-renderer'
import React, { useContext, useEffect, useState } from 'react'
import { GyanaEvents } from 'apps/base/javascript/events'
import { DnDContext, IDnDContext } from '../context'
import Tippy from '@tippyjs/react'
import { getWorkflowStatus, runWorkflow } from '../api'

const RunButton: React.FC = () => {
  const { workflowId, elements, setElements, setHasBeenRun, isOutOfDate, setIsOutOfDate } =
    useContext(DnDContext) as IDnDContext

  const hasOutput = elements.some((el) => el.type === 'output')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const update = () => setIsOutOfDate(true)
    window.addEventListener(GyanaEvents.UPDATE_WORKFLOW, update)
    return () => window.removeEventListener(GyanaEvents.UPDATE_WORKFLOW, update)
  }, [])

  const initCeleryProgress = (taskId: string) => {
    CeleryProgressBar.initProgressBar(`/celery-progress/${taskId}`, {
      onSuccess: () => {
        setElements((elements) =>
          elements.map((el) => {
            delete el.data.error
            return el
          })
        )
        setIsOutOfDate(false)
        setHasBeenRun(false)
        window.dispatchEvent(new Event(GyanaEvents.RUN_WORKFLOW))
        setLoading(false)
        alert('Workflow finished running!')
      },
      onError: async () => {
        const errors = (await getWorkflowStatus(workflowId)).errors
        setElements((elements) =>
          elements.map((el) => {
            if (isNode(el)) {
              const error = errors[parseInt(el.id)]
              // Add error to node if necessary
              if (error) {
                el.data['error'] = error
              }
              // Remove error if necessary
              else if (el.data.error) {
                delete el.data['error']
              }
            }
            return el
          })
        )
        setLoading(false)
        alert('Workflow failed running')
      },
      // override the defaults, otherwise they will raise errors
      onRetry: () => {},
      onProgress: () => {},
    })
  }

  return (
    <Tippy
      content={
        !hasOutput
          ? 'Workflow needs a Save Data node to run'
          : !isOutOfDate
          ? "You haven't made any new changes"
          : 'Run workflow to create or update your output data sources'
      }
    >
      <div className='dndflow__run-button'>
        <button
          data-cy='workflow-run'
          onClick={async () => {
            setLoading(true)
            const result = await runWorkflow(workflowId)
            initCeleryProgress(result.task_id)
          }}
          className='button button--sm button--success'
          disabled={!hasOutput || loading || !isOutOfDate}
        >
          {loading ? (
            <i className='fad fa-fw fa-spinner-third fa-spin' />
          ) : (
            <i className='fas fa-fw fa-play'></i>
          )}
          Run
        </button>
      </div>
    </Tippy>
  )
}

export default RunButton
