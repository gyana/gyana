import React, { useState } from 'react'
import ReactDOM from 'react-dom'
import ReactHtmlParser from 'react-html-parser'
import { Rnd as ReactRnd } from 'react-rnd'
let auth = new coreapi.auth.SessionAuthentication({
  csrfCookieName: 'csrftoken',
  csrfHeaderName: 'X-CSRFToken',
})

let client = new coreapi.Client({ auth: auth })

// Should be the same as in the grid-size controller
// TODO: somehow inject the value from the controller into this component
const GRID_COLS = 80

const GyWidget_: React.FC<{ children: React.ReactElement; root: HTMLElement }> = ({
  children,
  root,
}) => {
  const mode: 'view' | 'edit' | 'public' =
    new URLSearchParams(window.location.search).get('mode') ||
    window.location.href.includes('projects')
      ? 'edit'
      : 'public'
  const id = children.props['data-id']
  // Utilised to decide the clamping on interaction as well as clamps for placement
  const stepSize = Math.floor(root.offsetWidth / GRID_COLS)

  const [x, setX] = useState(() => parseInt(children.props['data-x']) || 0)
  const [y, setY] = useState(() => parseInt(children.props['data-y']) || 0)
  const [width, setWidth] = useState(() => parseInt(children.props['data-width']) || 200)
  const [height, setHeight] = useState(() => parseInt(children.props['data-height']) || 200)

  return (
    <ReactRnd
      data-zindex-target='entity'
      enableResizing={mode === 'edit'}
      disableDragging={mode !== 'edit'}
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
      size={{
        width,
        height,
      }}
      resizeGrid={[stepSize, stepSize]}
      dragGrid={[stepSize, stepSize]}
      minHeight='200'
      minWidth='200'
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
