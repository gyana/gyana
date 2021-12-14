import { createContext } from 'react'

export interface IAutomateContext {
  runInfo: { [key: number]: any }
}

export const AutomateContext = createContext<IAutomateContext | null>(null)
