import { createContext } from 'react'

export const DnDContext = createContext({
  workflowId: '',
  removeById: (id: string) => {},
  getIncomingNodes: (id: string): [Node, Node[]] | null => null,
  addNode: (node) => {},
})
