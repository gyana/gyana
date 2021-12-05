import { getApiClient } from 'apps/base/javascript/api'

import { ArrowHeadType, Connection, Edge, Node } from 'react-flow-renderer'

export const toNode = (res): Node => ({
  id: `${res.id}`,
  type: 'default',
  data: {},
  position: { x: 0, y: 0 },
})

export const getEdgeId = ({ source, sourceHandle, target, targetHandle }: Connection) =>
  `reactflow__edge-${source}${sourceHandle}-${target}${targetHandle}`

export const EDGE_DEFAULTS = { type: 'smoothstep', arrowHeadType: ArrowHeadType.ArrowClosed }

export const toEdge = (parent: number, child: number): Edge => {
  const edgeParams = {
    source: parent.toString(),
    sourceHandle: null,
    target: child.toString(),
    targetHandle: null,
  }
  return {
    id: getEdgeId(edgeParams),
    ...edgeParams,
    ...EDGE_DEFAULTS,
  }
}

const client = getApiClient()

export const listWorkflows = async (projectId: number) => {
  const result = await client.action(window.schema, ['workflows', 'api', 'workflows', 'list'], {
    project: projectId,
  })

  const nodes = result.results.map((r) => toNode(r))
  const edges = result.results
    .map((r) => r.parents.map((parent_id) => toEdge(parent_id, r.id)))
    .flat()

  return [nodes, edges]
}
