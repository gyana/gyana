import { createContext } from 'react'
import { Node } from 'react-flow-renderer'

export interface IDnDContext {
  workflowId: number
  elements
  setElements
  hasBeenRun: boolean
  setHasBeenRun: (hasBeenRun: boolean) => void
  isOutOfDate: boolean
  setIsOutOfDate: (isOutOfDate: boolean) => void
  setNeedsFitView: (needsFitView: boolean) => void
  removeById: (id: string) => void
  getIncomingNodes: (id: string) => [Node, Node[]]
  addNode: (data: any) => void
}

export const DnDContext = createContext<IDnDContext | null>(null)
