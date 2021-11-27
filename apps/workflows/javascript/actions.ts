import { getApiClient } from 'apps/base/javascript/api'
import { Node, Edge, XYPosition, Connection, ArrowHeadType } from 'react-flow-renderer'
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
  })

  return {
    id: `edge-${result.id}`,
    source: result.parent.toString(),
    sourceHandle: null,
    type: 'smoothstep',
    targetHandle: null,
    arrowHeadType: ArrowHeadType.ArrowClosed,
    target: result.child.toString(),
  }
}

export const updateEdgeAction = (edge: Edge, connection: Connection): void => {
  client.action(window.schema, ['nodes', 'api', 'edges', 'partial_update'], {
    id: edge.id.replace('edge-', ''),
    parent: connection.source,
    child: connection.target,
  })
}

export const deleteEdge = (edge: Edge): void => {
  client.action(window.schema, ['nodes', 'api', 'edges', 'delete'], {
    id: edge.id.replace('edge-', ''),
  })
}

export const listAll = async (workflowId: string): Promise<[Node[], Edge[]]> => {
  const result = await client.action(window.schema, ['nodes', 'api', 'nodes', 'list'], {
    workflow: workflowId,
  })
  const nodes = result.results.map((r) => toNode(r, { x: r.x, y: r.y }))
  const edges = result.results.map((r) => r.parents.map((parent) => toEdge(r, parent))).flat()
  return [nodes, edges]
}

export const getWorkflowStatus = (workflowId: string) => {
  return client.action(window.schema, ['workflows', 'out_of_date', 'list'], { id: workflowId })
}
