import { getApiClient } from 'apps/base/javascript/api'
import { Node, Edge, XYPosition, Connection, ArrowHeadType } from 'react-flow-renderer'
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

// CRUDL REST API operations for nodes and edges

const client = getApiClient()

export const createNode = async (
  workflowId: number,
  type: string,
  position: XYPosition
): Promise<Node> => {
  const result = await client.action(window.schema, ['nodes', 'api', 'nodes', 'create'], {
    kind: type,
    workflow: workflowId,
    x: position.x,
    y: position.y,
  })

  return toNode(result, position)
}

export const moveNode = (node: Node): void => {
  client.action(window.schema, ['nodes', 'api', 'nodes', 'partial_update'], {
    id: node.id,
    x: node.position.x,
    y: node.position.y,
  })
}

export const deleteNode = (node: Node): void => {
  client.action(window.schema, ['nodes', 'api', 'nodes', 'delete'], {
    id: node.id,
  })
}

export const createEdge = async (connection: Connection) => {
  const result = await client.action(window.schema, ['nodes', 'api', 'edges', 'create'], {
    parent: connection.source,
    child: connection.target,
    position: parseInt(connection.targetHandle as string),
  })

  return toEdge(result.id, result.parent, result.child, result.position)
}

export const updateEdge = (edge: Edge, connection: Connection): void => {
  client.action(window.schema, ['nodes', 'api', 'edges', 'partial_update'], {
    id: edge.data.id,
    parent: connection.source,
    child: connection.target,
    position: parseInt(connection.targetHandle as string),
  })
}

export const deleteEdge = (edge: Edge): void => {
  client.action(window.schema, ['nodes', 'api', 'edges', 'delete'], {
    id: edge.data.id,
  })
}

export const listAll = async (workflowId: string): Promise<[Node[], Edge[]]> => {
  const result = await client.action(window.schema, ['nodes', 'api', 'nodes', 'list'], {
    workflow: workflowId,
  })
  const nodes = result.results.map((r) => toNode(r, { x: r.x, y: r.y }))
  const edges = result.results
    .map((r) =>
      r.parents.map((parent) => toEdge(parent.id, parent.parent_id, r.id, parent.position))
    )
    .flat()
  return [nodes, edges]
}

export const getWorkflowStatus = (workflowId: string) => {
  return client.action(window.schema, ['workflows', 'out_of_date', 'list'], { id: workflowId })
}
