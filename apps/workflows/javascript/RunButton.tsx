import { Edge, isNode, Node } from 'react-flow-renderer'
import React, { useEffect, useState } from 'react'
import { GyanaEvents } from 'apps/base/javascript/events'

const RunButton: React.FC<{
  hasOutput: boolean
  hasBeenRun: boolean
  setHasBeenRun: (x: boolean) => void
  workflowId: string
  client
  elements: (Node | Edge)[]
  setElements: (elements: (Node | Edge)[]) => void
  isOutOfDate: boolean
  setIsOutOfDate: (x: boolean) => void
}> = ({
  hasOutput,
  hasBeenRun,
  setHasBeenRun,
  workflowId,
  client,
  elements,
  setElements,
  isOutOfDate,
  setIsOutOfDate,
}) => {
  const [loading, setLoading] = useState(false)
  useEffect(() => {
    const update = () => setIsOutOfDate(true)

    window.addEventListener(GyanaEvents.UPDATE_WORKFLOW, update)
    return () => window.removeEventListener(GyanaEvents.UPDATE_WORKFLOW, update)
  })

  return (
    <div className='dndflow__run-button'>
      <button
        disabled={!hasOutput || loading || !isOutOfDate}
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
        className='button button--sm button--outline button--success'
        data-controller='tooltip'
      >
        <i className='fas fa-fw fa-play'></i> Run
        {loading && (
          <div className='absolute m-auto'>
            <i className='fad fa-spinner-third fa-spin' />
          </div>
        )}
        <div data-tooltip-target='body'>
          {!hasOutput && hasBeenRun ? (
            <span>Workflow needs output node to run</span>
          ) : (
            <span>Run a workflow to use results in dashboards and other workflows.</span>
          )}
        </div>
      </button>
    </div>
  )
}

export default RunButton
