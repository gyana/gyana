import { isNode } from 'react-flow-renderer'
import React, { useContext, useEffect, useState } from 'react'
import { GyanaEvents } from 'apps/base/javascript/events'
import { getApiClient } from 'apps/base/javascript/api'
import { DnDContext, IDnDContext } from '../context'
import Tippy from '@tippyjs/react'

const client = getApiClient()

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

  const tooltip = !hasOutput
    ? 'Workflow needs a Save Data node to run'
    : !isOutOfDate
    ? "You haven't made any new changes"
    : 'Run workflow to create or update your output data sources'

  return (
    <Tippy content={tooltip}>
      <div className='dndflow__run-button'>
        <button
          onClick={() => {
            setLoading(true)

            client
              .action(window.schema, ['workflows', 'run_workflow', 'create'], {
                id: workflowId,
              })
              .then((res) => {
                if (res) {
                  setElements(
                    elements.map((el) => {
                      if (isNode(el)) {
                        const error = res[parseInt(el.id)]
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
                  if (Object.keys(res).length === 0) {
                    setIsOutOfDate(false)
                    setHasBeenRun(false)
                    window.dispatchEvent(new Event(GyanaEvents.RUN_WORKFLOW))
                  }
                  setLoading(false)
                }
                alert('Workflow finished running!')
              })
              .catch(() => {
                setLoading(false)
                alert('Workflow failed running')
              })
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
