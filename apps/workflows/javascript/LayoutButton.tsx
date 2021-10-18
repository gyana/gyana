import dagre from 'dagre'
import React, { useCallback } from 'react'
import { isNode, useStoreState, ControlButton } from 'react-flow-renderer'

const dagreGraph = new dagre.graphlib.Graph()
dagreGraph.setDefaultEdgeLabel(() => ({}))
dagreGraph.setGraph({ rankdir: 'LR' })

// Add some additional spacing for the absolute positioned buttons
const BUTTON_SPACING = 40

const LayoutButton: React.FC<{
  elements
  setElements
  client
  setViewHasChanged
  workflowId
}> = ({ elements, setElements, client, setViewHasChanged, workflowId }) => {
  const nodes = useStoreState((state) => state.nodes)

  const onLayout = useCallback(() => {
    const layoutedElements = getLayoutedElements(elements, nodes)
    setElements(layoutedElements)

    client.action(window.schema, ['workflows', 'update_positions', 'create'], {
      id: workflowId,
      nodes: layoutedElements
        .filter(isNode)
        .map((el) => ({ id: el.id, x: el.position.x, y: el.position.y })),
    })
    setViewHasChanged(true)
  }, [elements, nodes])

  return (
    <ControlButton onClick={onLayout}>
      <i title='Format workflow' className='fas fa-fw fa-sort-size-down'></i>
    </ControlButton>
  )
}

// TODO: we can simplify the logic here by moving this calculation to the backend.
// Inspired by https://reactflow.dev/examples/layouting/
const getLayoutedElements = (elements, nodes) => {
  elements.forEach((el) => {
    if (isNode(el)) {
      const node = nodes.find((node) => node.id === el.id)
      dagreGraph.setNode(el.id, {
        width: node.__rf.width,
        height: node.__rf.height + BUTTON_SPACING,
      })
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
        y: nodeWithPosition.y - (node.__rf.height + BUTTON_SPACING) / 2,
      }
    }

    return el
  })
}

export default LayoutButton
