import { createContext } from 'react'

export interface IAutomateContext {
  runInfo: { [key: number | string]: any }
}

export const AutomateContext = createContext<IAutomateContext | null>(null)
