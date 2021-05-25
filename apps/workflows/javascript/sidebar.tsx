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

export default () => {
  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <aside className='dnd-sidebar'>
      {Object.keys(SECTIONS).map((section) => (
        <>
          <hgroup>
            <h3>{section}</h3>
            <p>TODO: Section description</p>
          </hgroup>

          <div className='grid' style={{gridAutoRows: "1fr"}} key={section}>
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
          <hr/>
        </>
      ))}
    </aside>
  )
}
