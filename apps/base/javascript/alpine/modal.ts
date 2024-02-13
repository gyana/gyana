/**
 * Modal for rendering HTMX partials including forms.
 *
 * @example
 * <button x-modal="{% url '__url__' % }">Settings</button>
 */
export default (el, { value, modifiers, expression }, { cleanup }) => {
  const sizes = ['tall', 'wide', 'full']
  const classes = modifiers
    .filter((m) => sizes.includes(m))
    .map((m) => `modal--${m}`)
    .join(' ')

  const root = document.getElementById('modal')

  const open = () => {
    let changed = false
    let is_preview = false

    const modal = htmlToElement(
      modal_t.replace('__hx_get__', expression).replace('__class__', classes)
    )

    // TODO: decide how to handle persistance logic for tabs (i.e. widgets)
    // for now, this is a constraint to avoid duplicate modals
    root.replaceChildren(modal)

    // register HTMX attributes on the modal
    htmx.process(modal)

    // handle clicks outside of the modal or cross button
    modal?.addEventListener('click', (event) => {
      if (
        event.target === event.currentTarget ||
        event.target.closest('button')?.classList?.contains('modal__close')
      ) {
        // modal closing warning if content has changed
        if (changed) {
          const warning = htmlToElement(warning_t)

          warning.addEventListener('modal:close', () => {
            warning.remove()
            modal.remove()
          })

          warning.addEventListener('modal:stay', () => warning.remove())

          modal.insertAdjacentElement('afterend', warning)
        } else {
          // TODO: decide whether to implement autosave option for widgets and controls
          // Check for form with hx-post=expression and request submit
          modal.remove()

          const params = new URLSearchParams(location.search)
          params.delete('modal_item')
          history.replaceState(
            {},
            '',
            `${location.pathname}?${params.toString()}`
          )
        }
      }
    })

    // handle tab changes
    modal?.addEventListener('htmx:beforeRequest', function (event) {
      const { requestConfig, pathInfo } = event.detail
      if (
        pathInfo.requestPath.split('?')[0] === expression.split('?')[0] &&
        requestConfig.verb === 'get'
      ) {
        if (changed) {
          event.preventDefault()

          const warning = htmlToElement(warning_t)

          warning.addEventListener('modal:close', () => {
            warning.remove()
            changed = false
            // re-trigger the click event on tab
            event.target.click()
          })

          warning.addEventListener('modal:stay', () => warning.remove())

          modal.insertAdjacentElement('afterend', warning)
        }
      }
    })

    modal.addEventListener('change', (event) => {
      // ignore fields without name (e.g. search in input node)
      if (event.target.name !== '') changed = true
    })

    // close the modal if there is a successful POST request to the x-modal URL
    modal.addEventListener('htmx:afterRequest', (event) => {
      const { requestConfig, xhr } = event.detail

      if (
        [200, 201].includes(xhr.status) &&
        requestConfig.path.split('?')[0] === expression.split('?')[0] &&
        requestConfig.verb === 'post'
      ) {
        changed = false

        if (!is_preview) {
          modal.remove()

          if (modifiers.includes('reload')) {
            location.reload()
          }
        }
      }
    })

    modal.addEventListener('submit', (event) => {
      is_preview = event.submitter.value === 'Save & Preview'
    })

    // persistence - update URL with modal id
    if (modifiers.includes('persist')) {
      const params = new URLSearchParams(location.search)
      params.set('modal_item', parseModalId(expression))
      history.replaceState({}, '', `${location.pathname}?${params.toString()}`)
    }
  }

  // persistence - open modal if URL contains modal id
  if (modifiers.includes('persist')) {
    const params = new URLSearchParams(location.search)
    if (
      parseModalId(expression) == parseInt(params.get('modal_item')) &&
      // check that the modal is not already open
      !root.hasChildNodes()
    ) {
      open()
    }
  }

  el.addEventListener(value || 'click', open)

  cleanup(() => {
    // TODO: remove event listener, if necessary
    el.removeEventListener('click', open)
  })
}

const modal_t = /*html*/ `<div class="modal __class__">
  <div class="card card--none card--modal">
    <div class="overflow-hidden flex-1"
      hx-get="__hx_get__"
      hx-trigger="load"
      hx-target="this"
    >
      <div class="placeholder-scr placeholder-scr--fillscreen">
        <i class="placeholder-scr__icon fad fa-spinner-third fa-spin fa-2x"></i>
      </div>
    </div>
  </div>
</div>`

const warning_t = /*html*/ `<div class="modal flex items-center justify-center">
  <div class="card card--sm card--inline flex flex-col">
    <h3>Be careful!</h3>
    <p class="mb-7">You have unsaved changes that will be lost on closing!</p>
    <div class="flex flex-row gap-7">
      <button class="button button--success button--sm flex-1" @click="$dispatch('modal:stay')">
        Stay
      </button>
      <button class="button button--danger button--outline button--sm flex-1" @click="$dispatch('modal:close')">
        Close Anyway
      </button>
    </div>
  </div>
</div>`

const htmlToElement = (html) => {
  const template = document.createElement('template')
  template.innerHTML = html.trim()
  return template.content.firstChild as HTMLElement
}

function parseModalId(url) {
  const numbers = url.match(/\d+/g)

  if (numbers && numbers.length > 0) {
    const lastNumber = numbers[numbers.length - 1]
    return parseInt(lastNumber, 10)
  }

  return null
}
