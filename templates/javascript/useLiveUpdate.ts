import { useEffect, useRef } from 'react'

const useLiveUpdate = (optionId: string | number, selected: string | number) => {
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (inputRef.current && optionId != selected) {
      // Manually fire the input change event for live update form
      // https://stackoverflow.com/a/36648958/15425660
      inputRef.current.dispatchEvent(new Event('change', { bubbles: true }))
    }
  }, [optionId])

  return inputRef
}

export default useLiveUpdate
