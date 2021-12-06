import { useEffect, useState } from 'react'

const useRunProgress = (runTaskUrl: string, celeryProgressUrl: string) => {
  const [ready, setReady] = useState(false)
  const [runInfo, setRunInfo] = useState({})

  const init = () => {
    CeleryProgressBar.initProgressBar(runTaskUrl, {
      onSuccess: () => {
        setRunInfo((runInfo) => ({ ...runInfo, run: 'done' }))
      },
      onProgress: (_, __, progress) => {
        if (progress.description) {
          setRunInfo(JSON.parse(progress.description))
        }
      },
    })
    setReady(true)
  }

  useEffect(() => {
    if (!ready) {
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
