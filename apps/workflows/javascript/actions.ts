import { INode } from './interfaces'
import { getApiClient } from 'apps/base/javascript/api'
import { Node } from 'react-flow-renderer'
import { toEdge, toNode } from './serde'

const client = getApiClient()

const NODES = JSON.parse(document.getElementById('nodes').textContent) as INode

export const createNode = async (workflowId: number, type: string, position) => {
  const result = await client.action(window.schema, ['nodes', 'api', 'nodes', 'create'], {
    kind: type,
    workflow: workflowId,
    x: position.x,
    y: position.y,
  })

  return toNode(result, position)
}

export const moveNode = (node) => {
  client.action(window.schema, ['nodes', 'api', 'nodes', 'partial_update'], {
    id: node.id,
    x: node.position.x,
    y: node.position.y,
  })
}

export const deleteNode = (node: Node) => {
  client.action(window.schema, ['nodes', 'api', 'nodes', 'delete'], {
    id: node.id,
  })
}

export const updateParentEdges = (id: string, parents: string[]) =>
  client.action(window.schema, ['nodes', 'api', 'nodes', 'partial_update'], {
    id,
    parents: parents.map((p) => ({ parent_id: p })),
  })

export const listAll = async (workflowId: string) => {
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
