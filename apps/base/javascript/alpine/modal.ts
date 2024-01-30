/**
 * Modal for rendering HTMX partials including forms.
 *
 * @example
 * <button x-modal="{% url '__url__' % }">Settings</button>
 */
export default (el, { modifiers, expression }, { cleanup }) => {
  let changed = false

  const open = () => {
    const modal = html_to_element(modal_t.replace('__expression__', expression))

    el.insertAdjacentElement('afterend', modal)
    // register HTMX attributes on the modal
    htmx.process(modal)

    // handle clicks outside of the modal or cross button
    modal?.addEventListener('click', (event) => {
      if (
        event.target === event.currentTarget ||
        event.target.closest('button').classList.contains('tf-modal__close')
      ) {
        // modal closing warning if content has changed
        if (changed) {
          const warning = html_to_element(warning_t)

          warning.addEventListener('modal:close', () => {
            warning.remove()
            modal.remove()
          })

          warning.addEventListener('modal:stay', () => {
            warning.remove()
          })

          modal.insertAdjacentElement('afterend', warning)
        } else {
          modal.remove()
        }
      }
    })

    modal.addEventListener('change', (event) => {
      changed = true
    })

    // close the modal if there is a successful POST request to the x-modal URL
    modal.addEventListener('htmx:afterRequest', (event) => {
      const { requestConfig, xhr } = event.detail

      if (
        [200, 201].includes(xhr.status) &&
        requestConfig.path === expression &&
        requestConfig.verb === 'post'
      ) {
        modal.remove()
      }
    })

    // handle persistence
    if (modifiers.includes('persist')) {
      const params = new URLSearchParams(location.search)
      const modalItem = parseLastIntegerFromURL(expression)
      params.set('modal_item', modalItem)
      history.replaceState({}, '', `${location.pathname}?${params.toString()}`)
    }
  }

  if (modifiers.includes('persist')) {
    const params = new URLSearchParams(location.search)
    const modalItem = parseInt(params.get('modal_item'))
    if (parseLastIntegerFromURL(expression) == modalItem) {
      open()
    }
  }

  el.addEventListener('click', (event) => {
    open()
  })

  cleanup(() => {
    // TODO: remove event listener, if necessary
  })
}

const modal_t = /*html*/ `<div class="tf-modal">
  <div class="card card--none card--modal">
    <div class="overflow-hidden flex-1"
      hx-get="__expression__"
      hx-trigger="load"
      hx-target="this"
    >
      <div class="placeholder-scr placeholder-scr--fillscreen">
        <i class="placeholder-scr__icon fad fa-spinner-third fa-spin fa-2x"></i>
      </div>
    </div>
  </div>
</div>`

const warning_t = /*html*/ `<div class="tf-modal flex items-center justify-center">
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

const html_to_element = (html) => {
  const template = document.createElement('template')
  template.innerHTML = html.trim()
  return template.content.firstChild as HTMLElement
}

function parseLastIntegerFromURL(url) {
  const numbers = url.match(/\d+/g)

  if (numbers && numbers.length > 0) {
    const lastNumber = numbers[numbers.length - 1]
    return parseInt(lastNumber, 10)
  }

  return null
}
