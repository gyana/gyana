import { useEffect, useState } from 'react'

const useRunProgress = (runTaskUrl: string | undefined, celeryProgressUrl: string) => {
  const [ready, setReady] = useState(false)
  const [runInfo, setRunInfo] = useState({})

  const init = () => {
    CeleryProgressBar.initProgressBar(runTaskUrl, {
      onSuccess: () => {
        setRunInfo((runInfo) => {
          // refresh the page to keep run button in sync with react app
          if (Object.keys(runInfo).length > 0) Turbo.visit(window.location)
          return { ...runInfo, run: 'done' }
        })
      },
      // override the default, retries are used for connectors
      onRetry: () => {},
      onProgress: (_, __, progress) => {
        if (progress.description) {
          setRunInfo(JSON.parse(progress.description))
        }
      },
    })
    setReady(true)
  }

  useEffect(() => {
    if (!ready && runTaskUrl) {
      if (typeof CeleryProgressBar === 'undefined') {
        var script = document.createElement('script')
        script.src = celeryProgressUrl
        script.onload = () => window.dispatchEvent(new Event('celeryProgress:load'))
        document.head.appendChild(script)
        window.addEventListener('celeryProgress:load', init, { once: true })
      } else {
        init()
      }
    }
  }, [ready])

  return { runInfo }
}

export default useRunProgress
