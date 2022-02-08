import { useEffect, useState } from 'react'

export const GYANA_DEMO_STORE_EVENT = 'gyana:demo-store'

interface DemoStore {
  integrations: { id: string; name: string; icon_path: string }[]
  node: { id: string; name: string; icon: string } | null
}

declare global {
  interface Window {
    __demo_store__: DemoStore
  }
}

// Lightweight store for independent React web components
export const useDemoStore = (
  callback: (() => void) | undefined = undefined
): [DemoStore, (store: DemoStore) => void] => {
  // by default just force a re-render with dummy state update
  // https://stackoverflow.com/a/53837442/15425660
  const [value, setValue] = useState(0)

  const actualCallback = callback || (() => setValue((value) => value + 1))

  useEffect(() => {
    window.addEventListener(GYANA_DEMO_STORE_EVENT, actualCallback)
    return () => window.removeEventListener(GYANA_DEMO_STORE_EVENT, actualCallback)
  }, [])

  const setDemoStore = (store: DemoStore) => {
    window.__demo_store__ = store
    window.dispatchEvent(new CustomEvent(GYANA_DEMO_STORE_EVENT))
  }

  return [window.__demo_store__, setDemoStore]
}
