import { Edge, Node, getIncomers, isNode, isEdge } from 'react-flow-renderer'
import { NODES } from './interfaces'

type Element = Node | Edge

export const canAddEdge = (elements: Element[], target: string) => {
  const targetElement = elements.find((el) => isNode(el) && el.id === target) as Node
  if (targetElement) {
    const incomingNodes = getIncomers(targetElement, elements)

    // Node arity is defined in nodes/bigquery.py
    // Join (2), Union/Except/Insert (-1 = Inf), otherwise (1)
    const maxParents = NODES[targetElement.data.kind].maxParents

    if (maxParents === -1 || incomingNodes.length < maxParents) {
      return true
    } else {
      // TODO: Add notification here
      // alert("You can't add any more incoming edges to this node")
      return false
    }
  }
}

export const addEdgeToParents = (elements: Element[], source: string, target: string) => {
  return [
    ...elements.filter((el) => isEdge(el) && el.target === target).map((el) => (el as Edge).source),
    source,
  ]
}

export const removeEdgeFromParents = (elements: Element[], edge: Edge) => {
  return elements
    .filter((el) => isEdge(el) && el.target === edge.target && el.source !== edge.source)
    .map((el) => (el as Edge).source)
}

export const updateEdgeSourceInParents = (elements: Element[], oldEdge: Edge) => {
  return elements
    .filter((el) => isEdge(el) && el.target === oldEdge.target && el.source !== oldEdge.source)
    .map((el) => (el as Edge).source)
}

export const updateEdgeTargetInParents = (
  elements: Element[],
  oldEdge: Edge,
  source: string,
  target: string
) => {
  const oldParents = elements
    .filter((el) => isEdge(el) && el.target === oldEdge.target && el.source !== oldEdge.source)
    .map((el) => (el as Edge).source)

  const newParents = [
    ...elements.filter((el) => isEdge(el) && el.target === target).map((el) => (el as Edge).source),
    source,
  ]

  return [oldParents, newParents]
}
