import React, { useState } from 'react'
import ReactDOM from 'react-dom'
import ReactHtmlParser from 'react-html-parser'
import { Rnd as ReactRnd } from 'react-rnd'
let auth = new coreapi.auth.SessionAuthentication({
  csrfCookieName: 'csrftoken',
  csrfHeaderName: 'X-CSRFToken',
})

let client = new coreapi.Client({ auth: auth })

// The grid layout (on any screen) has 20 columns
const GRID_COLS = 40

const GyWidget_: React.FC<{ children: React.ReactElement; root: HTMLElement }> = ({
  children,
  root,
}) => {
  const mode = new URLSearchParams(window.location.search).get('mode') || 'edit'
  const id = children.props['data-id']
  // Utilised to decide the clamping on interaction as well as clamps for placement
  const stepSize = Math.floor(root.offsetWidth / GRID_COLS)
  const [x, setX] = useState(
    () => (parseInt(children.props['data-x']) * root.clientWidth) / 100 || 0
  )
  const [y, setY] = useState(() => parseInt(children.props['data-y']) || 0)
  const [width, setWidth] = useState(
    () => (parseInt(children.props['data-width']) * root.clientWidth) / 100 || 200
  )
  const [height, setHeight] = useState(() => parseInt(children.props['data-height']) || 200)

  return (
    <ReactRnd
      data-zindex-target='entity'
      enableResizing={mode !== 'view'}
      disableDragging={mode === 'view'}
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
          x: Math.floor((newX / root.clientWidth) * 100),
          width: Math.floor((newWidth / root.clientWidth) * 100),
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
          x: Math.floor((newX / root.clientWidth) * 100),
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
