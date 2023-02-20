// Add loading indicator on form submission

document.addEventListener('submit', (event) => {
  const submitter = event.submitter

  if (submitter && !submitter.disabled) {
    const placeholder = document.createElement('template')
    placeholder.innerHTML = `
      <div class="placeholder-scr--inline">
        <i
          class="fad fa-spinner-third fa-spin"
          style="color: ${window
            .getComputedStyle(submitter)
            .getPropertyValue('color')};"
        ></i>
      </div>
    `.trim()

    submitter.style.position = 'relative'
    submitter.style.color = 'transparent'
    submitter.appendChild(placeholder.content.firstChild)

    for (const el of event.target.querySelectorAll('button[type=submit]'))
      el.disabled = true
  }
})

export {}
