import { getApiClient } from 'apps/base/javascript/api'

import { ArrowHeadType, Connection, Edge, Node } from 'react-flow-renderer'

export const toNode = (res): Node => {
  return {
    id: res.entity_id.toString(),
    // e.g. "workflows_workflow-1"
    type: res.entity_id.toString().split('-')[0].split('_')[1],
    data: res,
    position: { x: 0, y: 0 },
  }
}

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

export const getIntegration = async (id: number) => {
  return await client.action(window.schema, ['integrations', 'api', 'integrations', 'read'], { id })
}

export const getWorkflow = async (id: number) => {
  return await client.action(window.schema, ['workflows', 'api', 'workflows', 'read'], { id })
}

export const listProjectAll = async (projectId: number) => {
  const entities = await Promise.all([
    client.action(window.schema, ['integrations', 'api', 'integrations', 'list'], {
      project: projectId,
    }),
    client.action(window.schema, ['workflows', 'api', 'workflows', 'list'], {
      project: projectId,
    }),
    client.action(window.schema, ['dashboards', 'api', 'dashboards', 'list'], {
      project: projectId,
    }),
  ])

  const results = entities.map((r) => r.results).flat()

  const nodes = results.map((r) => toNode(r))
  const edges = results
    .map((r) => (r.parents || []).map((parent_id) => toEdge(parent_id, r.entity_id)))
    .flat()

  return [nodes, edges]
}

export const runProject = (projectId: number) => {
  return client.action(window.schema, ['projects', 'run', 'create'], {
    project_id: projectId,
  })
}
