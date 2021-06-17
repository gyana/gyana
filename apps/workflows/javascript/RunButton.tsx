import { Edge, isNode, Node } from 'react-flow-renderer'
import React, { useState } from 'react'

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

  return (
    <div className='dndflow__run-button'>
      <button
        disabled={!hasOutput || loading}
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
                  window.dispatchEvent(new Event('workflow-run'))
                }
                setLoading(false)
              }
            })
            .catch(() => setLoading(false))
        }}
        className='button button--outline button--success tooltip tooltip--bottom'
      >
        {loading && (
          <div className='absolute m-auto'>
            <i className='fad fa-spinner-third fa-spin' />
          </div>
        )}
        <div className={loading ? 'invisible' : undefined}>
          Run
          {isOutOfDate && hasOutput && hasBeenRun && (
            <>
              <div
                title='This workflow has been updated since the last run'
                className='absolute -top-3 -right-3 text-orange'
              >
                <i className='fas fa-exclamation-triangle bg-white p-1' />
              </div>
              <span className='tooltip__content'>Workflow needs output node to run</span>
            </>
          )}
        </div>
      </button>
    </div>
  )
}

export default RunButton
