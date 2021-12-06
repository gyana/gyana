import { useEffect, useState } from 'react'

const useRunProgress = (runTaskUrl: string, celeryProgressUrl: string) => {
  const [ready, setReady] = useState(false)

  const init = () => {
    CeleryProgressBar.initProgressBar(runTaskUrl, {
      onSuccess: () => console.log('Done'),
      onProgress: () => console.log('Progress'),
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

  return {}
}

export default useRunProgress
