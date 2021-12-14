import { createContext } from 'react'

export interface IScheduleContext {
  runInfo: { [key: number]: any }
}

export const ScheduleContext = createContext<IScheduleContext | null>(null)
