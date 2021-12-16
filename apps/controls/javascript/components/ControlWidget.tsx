import { getApiClient } from 'apps/base/javascript/api'
import React, { useState } from 'react'
import ReactDOM from 'react-dom'
import ReactHtmlParser from 'react-html-parser'
import { Rnd as ReactRnd } from 'react-rnd'

const client = getApiClient()
const WIDTH = 300
const HEIGHT = 100

const ControlWidget_: React.FC<{ children: React.ReactElement; root: HTMLElement }> = ({
  children,
  root,
}) => {
  const mode: 'view' | 'edit' | 'public' =
    (new URLSearchParams(window.location.search).get('mode') as 'view' | 'edit') ||
    (window.location.href.includes('projects') ? 'edit' : 'public')
  const id = children.props['data-id']

  // Utilised to decide the clamping on interaction as well as clamps for placement
  const stepSize = children.props['data-grid-size'] || 15

  const [x, setX] = useState(() => parseInt(children.props['data-x']) || 0)
  const [y, setY] = useState(() => parseInt(children.props['data-y']) || 0)

  return (
    <ReactRnd
      data-widget-list-target='widget'
      enableResizing={false}
      disableDragging={mode !== 'edit'}
      default={{
        width: WIDTH,
        height: HEIGHT,
        x,
        y,
      }}
      position={{
        x,
        y,
      }}
      bounds={'#dashboard-widget-container'}
      dragGrid={[stepSize, stepSize]}
      onDragStop={(e, { node, x, y, ...rest }) => {
        const parent = root
        // Snaps the x value within bounds of the parent
        const newX = Math.floor(
          x < 0
            ? 0
            : parent && x + node.clientWidth > parent.offsetWidth
            ? parent.offsetWidth - node.clientWidth
            : Math.round(x / stepSize) * stepSize
        )
        // Snaps the y value to the top of the parent element
        const newY = Math.floor(y > 0 ? Math.round(y / stepSize) * stepSize : 0)
        setX(newX)
        setY(newY)

        client.action(window.schema, ['controls', 'api', 'partial_update'], {
          id,
          x: Math.floor(newX),
          y: newY,
        })
      }}
    >
      {children}
    </ReactRnd>
  )
}

class ControlWidget extends HTMLElement {
  connectedCallback() {
    console.assert(!!this.parentElement, 'gy-control-widget requires a container element')
    const children = ReactHtmlParser(this.innerHTML)
    console.assert(children.length === 1, 'gy-control-widget requires only one child element')

    ReactDOM.render(
      <ControlWidget_ root={this.parentElement as HTMLElement}>{children[0]}</ControlWidget_>,
      this
    )
  }

  disconnectedCallback() {
    ReactDOM.unmountComponentAtNode(this)
  }
}

export default ControlWidget
