import { createContext } from 'react'

export interface IDnDContext {
  workflowId: number
  elements
  setElements
  hasBeenRun: boolean
  setHasBeenRun: (hasBeenRun: boolean) => void
  isOutOfDate: boolean
  setIsOutOfDate: (isOutOfDate: boolean) => void
  removeById: (id: string) => void
  getIncomingNodes: (id: string) => [Node, Node[]] | null
  addNode: (data: any) => void
}

export const DnDContext = createContext<IDnDContext | null>(null)
