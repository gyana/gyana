import { useEffect, useRef } from 'react'

const useLiveUpdate = (optionId: string | number, selected: string | number) => {
  const inputRef = useRef<HTMLInputElement>(null)
  const hasChangedRef = useRef(false)

  useEffect(() => {
    if (optionId !== selected) {
      hasChangedRef.current = true
    }
  }, [optionId])

  useEffect(() => {
    if (inputRef.current && hasChangedRef.current) {
      // Manually fire the input change event for live update form
      // https://stackoverflow.com/a/36648958/15425660
      inputRef.current.dispatchEvent(new Event('change', { bubbles: true }))
    }
  }, [optionId])

  return inputRef
}

export default useLiveUpdate
