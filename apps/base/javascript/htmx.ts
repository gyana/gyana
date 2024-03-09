// Support HTMX swap for 400/422 for invalid form submissions
// https://gist.github.com/lysender/a36143c002a84ed2c166bf7567b1a913
document.addEventListener('htmx:beforeSwap', function (evt) {
  if (evt.detail.xhr.status === 422 || evt.detail.xhr.status === 400) {
    evt.detail.shouldSwap = true
    evt.detail.isError = false
  }
})

export {}
