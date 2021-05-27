import React from 'react'
import { Edge, isNode, Node } from 'react-flow-renderer'
import { INode } from './interfaces'

import './styles/_dnd-sidebar.scss'

const NODES = JSON.parse(document.getElementById('nodes').textContent) as INode

const SECTIONS = Object.keys(NODES).reduce((sections, key) => {
  const node = NODES[key]
  const section = node.section

  if (!sections[section]) {
    sections[section] = [key]
  } else {
    sections[section] = [...sections[section], key]
  }

  return sections
}, {})

const Sidebar: React.FC<{
  hasOutput: boolean
  workflowId: string
  client
  elements: (Node | Edge)[]
  setElements: (elements: (Node | Edge)[]) => void
  isOutOfDate: boolean
  setIsOutOfDate: (x: boolean) => void
}> = ({ hasOutput, workflowId, client, elements, setElements, isOutOfDate, setIsOutOfDate }) => {
  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <aside className='dnd-sidebar'>
      <div className='dnd-sidebar__top'>
        <button
          disabled={!hasOutput}
          onClick={() =>
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
                    window.dispatchEvent(new Event('workflow-run'))
                  }
                }
              })
          }
          title='Workflow needs output node to run'
          className='button button--sm button--green button--square relative'
        >
          Run
          {isOutOfDate && (
            <div
              title='This workflow has been updated since the last run'
              className='absolute -top-3 -right-3 text-orange'
            >
              <i className='fas fa-exclamation-triangle bg-white p-1' />
            </div>
          )}
        </button>
      </div>

      <hgroup>
        <h2>Nodes</h2>
        <p>You can drag these onto the pane on your left.</p>
      </hgroup>

      {Object.keys(SECTIONS).map((section) => (
        <React.Fragment key={section}>
          <hgroup>
            <h3>{section}</h3>
            <p>TODO: Section description</p>
          </hgroup>

          <div className='grid' style={{ gridAutoRows: '1fr' }} key={section}>
            {SECTIONS[section].map((kind) => {
              const node = NODES[kind]

              return (
                <div
                  key={kind}
                  className='dnd-sidebar__node '
                  onDragStart={(event) => onDragStart(event, kind)}
                  draggable
                >
                  <i className={`dnd-sidebar__icon fad fa-fw ${node.icon}`}></i>
                  <div className='flex flex-col'>
                    <h4 className='dnd-sidebar__name'>{node.displayName}</h4>
                    <p className='dnd-sidebar__description'>{node.description}</p>
                  </div>
                </div>
              )
            })}
          </div>
          <hr />
        </React.Fragment>
      ))}
    </aside>
  )
}

export default Sidebar
