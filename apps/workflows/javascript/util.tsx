export const addParam = (key, value) => {
  const params = new URLSearchParams(location.search)
  params.set(key, value)
  history.replaceState({}, '', `${location.pathname}?${params.toString()}`)
}

export const removeParam = (key) => {
  const params = new URLSearchParams(location.search)
  params.delete(key)
  history.replaceState({}, '', `${location.pathname}?${params.toString()}`)
}
