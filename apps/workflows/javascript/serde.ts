import { Node, Edge, XYPosition, ArrowHeadType } from 'react-flow-renderer'
import { NODES } from './interfaces'

// Utilities to convert from coreapi JSON response to react-flow-renderer

export const toNode = (res, position: XYPosition): Node => ({
  id: `${res.id}`,
  type: ['input', 'output', 'text'].includes(res.kind) ? res.kind : 'default',
  data: {
    label: res.name || NODES[res.kind].displayName,
    icon: NODES[res.kind].icon,
    kind: res.kind,
    error: res.error,
    ...(res.kind === 'text' ? { text: res.text_text } : {}),
    description: res.description,
  },
  position,
})

export const toEdge = (id: number, parent: number, child: number, position: number): Edge => {
  return {
    id: `reactflow__edge-${parent}${position}-${child}null`,
    source: parent.toString(),
    sourceHandle: null,
    type: 'smoothstep',
    targetHandle: parent.toString(),
    arrowHeadType: ArrowHeadType.ArrowClosed,
    target: child.toString(),
    data: {
      id,
    },
  }
}
