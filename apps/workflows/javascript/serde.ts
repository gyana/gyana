import { Node, Edge, Position } from 'react-flow-renderer'
import { INode } from './interfaces'
const NODES = JSON.parse(document.getElementById('nodes').textContent) as INode

export const toNode = (res, position): Node => ({
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

export const toEdge = (node, parent): Edge => {
  return {
    id: `reactflow__edge-${parent.parent_id}null-${node.id}null`,
    source: parent.parent_id.toString(),
    sourceHandle: null,
    type: 'smoothstep',
    targetHandle: null,
    arrowHeadType: 'arrowclosed',
    target: node.id.toString(),
  }
}
