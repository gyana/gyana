import { createContext } from 'react'

export interface IDnDContext {
  workflowId: number
  elements
  setElements
  hasBeenRun: boolean
  setHasBeenRun: (hasBeenRun: boolean) => void
  isOutOfDate: boolean
  setIsOutOfDate: (isOutOfDate: boolean) => void
  setNeedsFitView: (needsFitView: boolean) => void
  deleteNodeById: (id: string) => void
  duplicateNode: (id: string) => void
}

export const DnDContext = createContext<IDnDContext | null>(null)
