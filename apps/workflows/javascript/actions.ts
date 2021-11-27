import { getApiClient } from 'apps/base/javascript/api'
import { Node, Edge, XYPosition, Connection } from 'react-flow-renderer'
import { toEdge, toNode } from './serde'

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
