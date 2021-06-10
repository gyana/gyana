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
const GRID_COLS = 20

const RndElement: React.FC<{ children: React.ReactElement; root: HTMLElement }> = ({
  children,
  root,
}) => {
  const id = children.props['data-id']
  const stepSize = root.offsetWidth / GRID_COLS
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
      resizeGrid={[stepSize, 10]}
      dragGrid={[stepSize, 10]}
      minHeight='200'
      minWidth='200'
      dragHandleClassName='rnd-handle'
      onResizeStop={(...args) => {
        const node = args[2]
        const parent = node.parentElement as HTMLElement
        const width = node.offsetWidth,
          height = node.offsetHeight
        const { x } = args[4]

        const newWidth = width > parent.offsetWidth ? parent.offsetWidth : width

        setWidth(newWidth)
        setHeight(height)

        const newX = x + newWidth > parent.offsetWidth ? parent.offsetWidth - newWidth : x
        setX(newX)

        client.action(window.schema, ['widgets', 'api', 'partial_update'], {
          id,
          x: Math.floor((newX / root.clientWidth) * 100),
          width: Math.floor((newWidth / root.clientWidth) * 100),
          height: height,
        })
      }}
      onDragStop={(e, { node, x, y }) => {
        const parent = node.parentElement
        // Snaps the x value within bounds of the parent
        const newX = Math.floor(
          x < 0
            ? 0
            : parent && x + node.clientWidth > parent.offsetWidth
            ? parent.offsetWidth - node.clientWidth
            : x
        )
        // Snaps the y value to the top of the parent element
        const newY = Math.floor(y > 0 ? y : 0)
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

const Rnd_: React.FC<{ children: React.ReactElement[]; root: HTMLElement }> = ({
  children,
  root,
}) => {
  return (
    <>
      {children?.map((child, idx) => (
        <RndElement key={idx} root={root}>
          {child}
        </RndElement>
      ))}
    </>
  )
}

class Rnd extends HTMLElement {
  connectedCallback() {
    this.style.position = 'relative'
    this.style.display = 'block'
    this.style.width = '100%'
    this.style.height = '100%'
    this.style.overflowX = 'hidden'
    this.style.overflowY = 'auto'

    ReactDOM.render(<Rnd_ root={this}>{ReactHtmlParser(this.innerHTML)}</Rnd_>, this)
  }
}

export default Rnd
