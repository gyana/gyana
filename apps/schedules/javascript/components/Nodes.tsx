import React from 'react'
import { Handle, NodeProps, Position } from 'react-flow-renderer'

const IntegrationNode: React.FC<NodeProps> = () => (
  <>
    <i className='fas fa-fw fa-database'></i>
    <Handle type='source' position={Position.Right} />
  </>
)

const WorkflowNode: React.FC<NodeProps> = () => (
  <>
    <Handle type='target' position={Position.Left} />
    <i className='fas fa-fw fa-sitemap'></i>
    <Handle type='source' position={Position.Right} />
  </>
)

const DashboardNode: React.FC<NodeProps> = () => (
  <>
    <Handle type='target' position={Position.Left} />
    <i className='fas fa-fw fa-chart-pie'></i>
  </>
)

const defaultNodeTypes = {
  integration: IntegrationNode,
  workflow: WorkflowNode,
  dashboard: DashboardNode,
}

export default defaultNodeTypes
