import dagre from 'dagre'
import { isNode, Edge, Node, Position } from 'react-flow-renderer'

const dagreGraph = new dagre.graphlib.Graph()
dagreGraph.setDefaultEdgeLabel(() => ({}))
dagreGraph.setGraph({ rankdir: 'LR' })

// Add some additional spacing for the absolute positioned buttons
const BUTTON_SPACING = 40

// TODO: we can simplify the logic here by moving this calculation to the backend.
// Inspired by https://reactflow.dev/examples/layouting/
export const getLayoutedElements = (elements: (Node | Edge)[], nodes: Node[]) => {
  elements.forEach((el) => {
    if (isNode(el)) {
      const node = nodes.find((node) => node.id === el.id) as Node
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
      el.targetPosition = Position.Left
      el.sourcePosition = Position.Right
      const node = nodes.find((node) => node.id === el.id) as Node

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
