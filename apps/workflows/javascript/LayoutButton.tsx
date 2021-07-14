import dagre from 'dagre'
import React, { useCallback } from 'react'
import { isNode, useStoreState, useZoomPanHelper } from 'react-flow-renderer'

const dagreGraph = new dagre.graphlib.Graph()
dagreGraph.setDefaultEdgeLabel(() => ({}))
dagreGraph.setGraph({ rankdir: 'LR' })

const LayoutButton: React.FC<{
  elements
  setElements
  client
  setViewHasChanged
}> = ({ elements, setElements, client, setViewHasChanged }) => {
  const nodes = useStoreState((state) => state.nodes)

  const onLayout = useCallback(() => {
    const layoutedElements = getLayoutedElements(elements, nodes)
    setElements(layoutedElements)

    client.action(window.schema, ['nodes', 'update_positions', 'create'], {
      nodes: layoutedElements
        .filter(isNode)
        .map((el) => ({ id: el.id, x: el.position.x, y: el.position.y })),
    })
    setViewHasChanged(true)
  }, [elements, nodes])

  return (
    <div className='dndflow__order-button'>
      <button className='button button--tertiary' onClick={onLayout}>
        Format
      </button>
    </div>
  )
}

// TODO: we can simplify the logic here by moving this calculation to the backend.
// Inspired by https://reactflow.dev/examples/layouting/
const getLayoutedElements = (elements, nodes) => {
  elements.forEach((el) => {
    if (isNode(el)) {
      const node = nodes.find((node) => node.id === el.id)
      dagreGraph.setNode(el.id, { width: node.__rf.width, height: node.__rf.height })
    } else {
      dagreGraph.setEdge(el.source, el.target)
    }
  })

  dagre.layout(dagreGraph)

  return elements.map((el) => {
    if (isNode(el)) {
      const nodeWithPosition = dagreGraph.node(el.id)
      el.targetPosition = 'left'
      el.sourcePosition = 'right'
      const node = nodes.find((node) => node.id === el.id)
      // unfortunately we need this little hack to pass a slightly different position
      // to notify react flow about the change. Moreover we are shifting the dagre node position
      // (anchor=center center) to the top left so it matches the react flow node anchor point (top left).
      el.position = {
        x: nodeWithPosition.x - node.__rf.width / 2 + Math.random() / 1000,
        y: nodeWithPosition.y - node.__rf.height / 2,
      }
    }

    return el
  })
}

export default LayoutButton
