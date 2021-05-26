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
}> = ({ hasOutput, workflowId, client, elements, setElements }) => {
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
                }
              })
          }
          title='Workflow needs output node to run'
          className='button button--sm button--green button--square'
        >
          Run
        </button>
      </div>
      <hgroup>
        <h2>Nodes</h2>
        <p>You can drag these onto the pane on your left.</p>
      </hgroup>

      {Object.keys(SECTIONS).map((section) => (
        <div className='flex flex-col' key={section}>
          <span className='font-semibold text-lg'>{section}</span>
          {SECTIONS[section].map((kind) => {
            const node = NODES[kind]

            return (
              <div
                key={kind}
                className='dnd-sidebar__node '
                onDragStart={(event) => onDragStart(event, kind)}
                draggable
              >
                <i className={`dnd-sidebar__icon fad ${node.icon}`}></i>
                <div className='flex flex-col'>
                  <h3 className='dnd-sidebar__name'>{node.displayName}</h3>
                  <p className='dnd-sidebar__description'>{node.description}</p>
                </div>
              </div>
            )
          })}
        </div>
      ))}
    </aside>
  )
}

export default Sidebar
