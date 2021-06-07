import React from 'react'
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

const Sidebar: React.FC = () => {
  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <aside className='dnd-sidebar'>
      <hgroup>
        <h2>Nodes</h2>
        <p>You can drag these onto the pane on your left.</p>
      </hgroup>

      {Object.keys(SECTIONS).map((section) => (
        <React.Fragment key={section}>
          <hgroup>
            <h3>{section}</h3>
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
