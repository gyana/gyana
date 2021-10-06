import { getApiClient } from 'apps/base/javascript/api'
import React, { useState } from 'react'
import ReactDOM from 'react-dom'
import ReactHtmlParser from 'react-html-parser'
import { Rnd as ReactRnd } from 'react-rnd'

const client = getApiClient()

// Should be the same as in the _widget.scss
const GRID_SIZE = 15

const GyWidget_: React.FC<{ children: React.ReactElement; root: HTMLElement }> = ({
  children,
  root,
}) => {
  const mode: 'view' | 'edit' | 'public' =
    (new URLSearchParams(window.location.search).get('mode') as 'view' | 'edit') ||
    (window.location.href.includes('projects') ? 'edit' : 'public')
  const id = children.props['data-id']

  // Utilised to decide the clamping on interaction as well as clamps for placement
  const stepSize = GRID_SIZE

  const [x, setX] = useState(() => parseInt(children.props['data-x']) || 0)
  const [y, setY] = useState(() => parseInt(children.props['data-y']) || 0)
  const [width, setWidth] = useState(() => parseInt(children.props['data-width']) || 200)
  const [height, setHeight] = useState(() => parseInt(children.props['data-height']) || 200)

  return (
    <ReactRnd
      data-widget-list-target='widget'
      enableResizing={mode === 'edit'}
      disableDragging={mode !== 'edit'}
      resizeHandleClasses={{
        top: 'widget-card__indicator',
        topLeft: 'widget-card__indicator',
        topRight: 'widget-card__indicator',
        bottom: 'widget-card__indicator',
        bottomLeft: 'widget-card__indicator',
        bottomRight: 'widget-card__indicator',
        left: 'widget-card__indicator',
        right: 'widget-card__indicator',
      }}
      resizeHandleComponent={{
        top: (<span></span>),
        topLeft: (<span></span>),
        topRight: (<span></span>),
        bottom: (<span></span>),
        bottomLeft: (<span></span>),
        bottomRight: (<span></span>),
        left: (<span></span>),
        right: (<span></span>),
      }}
      default={{
        width,
        height,
        x,
        y,
      }}
      position={{
        x,
        y,
      }}
      bounds={'#dashboard-widget-container'}
      size={{
        width,
        height,
      }}
      resizeGrid={[stepSize, stepSize]}
      dragGrid={[stepSize, stepSize]}
      minWidth='200'
      minHeight='45'
      onResizeStop={(...args) => {
        const node = args[2]
        const parent = root
        // Clamp the dimensions to the allowed stepSize/grid
        const width = Math.round(node.offsetWidth / stepSize) * stepSize,
          height = Math.round(node.offsetHeight / stepSize) * stepSize
        const { x } = args[4]

        const newWidth = width > parent.offsetWidth ? parent.offsetWidth : width

        setWidth(newWidth)
        setHeight(height)

        const newX =
          x + newWidth > parent.offsetWidth
            ? parent.offsetWidth - newWidth
            : Math.round(x / stepSize) * stepSize
        setX(newX)

        client.action(window.schema, ['widgets', 'api', 'partial_update'], {
          id,
          x: Math.floor(newX),
          width: Math.floor(newWidth),
          height: height,
        })
      }}
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

        client.action(window.schema, ['widgets', 'api', 'partial_update'], {
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

class GyWidget extends HTMLElement {
  connectedCallback() {
    console.assert(!!this.parentElement, 'gy-widget requires a container element')
    const children = ReactHtmlParser(this.innerHTML)
    console.assert(children.length === 1, 'gy-widget requires only one child element')

    ReactDOM.render(
      <GyWidget_ root={this.parentElement as HTMLElement}>{children[0]}</GyWidget_>,
      this
    )
  }
}

export default GyWidget
