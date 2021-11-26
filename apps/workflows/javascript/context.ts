import { createContext } from 'react'

export const NodeContext = createContext({
  removeById: (id: string) => {},
  getIncomingNodes: (id: string): [Node, Node[]] | null => null,
  addNode: (node) => {},
  workflowId: '',
})
