'use strict'
import { useEffect, useState } from 'react'

const PAUSE = 200
const MAX_TIME = 5000

export const useBlockUntilSchemaReady = () => {
  const [finishedPinging, setFinishedPinging] = useState(false)

  useEffect(() => {
    const checkSchemaExists = async () => {
      for (let time = 0; time < MAX_TIME; time += PAUSE) {
        if (window.schema) break
        await new Promise((resolve) => setTimeout(resolve, PAUSE))
      }
      setFinishedPinging(true)
    }
    checkSchemaExists()
  }, [])

  return { finishedPinging, schemaReady: !!window.schema }
}
