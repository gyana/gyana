/**
 * Simple Tippy.js stimulus wrapper.
 *
 * @example
 * <p x-modal="{% ...url... %}"/>
 *
 * @example
 * <p x-modal.persist="{% ...url... %}"/>
 */
export default (el, { modifiers, expression }, { cleanup }) => {
  let changed = false

  el.addEventListener('click', (event) => {
    const modal = document.createElement('div')
    modal.setAttribute('class', 'tf-modal')

    modal.innerHTML = `<div class="card card--none card--modal">
        <div class="overflow-hidden flex-1"
          hx-get="${expression}"
          hx-trigger="load"
          hx-target="this"
        >
          <div class="placeholder-scr placeholder-scr--fillscreen">
            <i class="placeholder-scr__icon fad fa-spinner-third fa-spin fa-2x"></i>
          </div>
        </div>
      </div>`

    el.insertAdjacentElement('afterend', modal)
    // register HTMX attributes on the modal
    htmx.process(modal)

    const close = () => {
      if (changed) {
        const warning = document.createElement('div')
        warning.setAttribute(
          'class',
          'tf-modal flex items-center justify-center'
        )
        warning.innerHTML = `<div class="card card--sm card--inline flex flex-col">
          <h3>Be careful!</h3>
          <p class="mb-7">You have unsaved changes that will be lost on closing!</p>
          <div class="flex flex-row gap-7">
            <button class="button button--success button--sm flex-1">
              Stay
            </button>
            <button class="button button--danger button--outline button--sm flex-1">
              Close Anyway
            </button>
          </div>
        </div>`

        warning.addEventListener('click', (event) => {
          if (event.target.classList.contains('button--success')) {
            warning.remove()
          }
          if (event.target.classList.contains('button--danger')) {
            warning.remove()
            modal.remove()
          }
        })

        modal.insertAdjacentElement('afterend', warning)
      } else {
        modal.remove()
      }
    }

    modal?.addEventListener('click', (event) => {
      if (
        event.target === event.currentTarget ||
        event.target.closest('button').classList.contains('tf-modal__close')
      ) {
        close()
      }
    })

    modal.addEventListener('change', (event) => {
      changed = true
    })

    modal.addEventListener('htmx:afterRequest', (event) => {
      const { requestConfig, xhr } = event.detail

      if (
        [200, 201].includes(xhr.status) &&
        requestConfig.path === expression &&
        requestConfig.verb === 'post'
      ) {
        close()
      }
    })
  })

  cleanup(() => {
    // TODO: remove event listener, if necessary
  })

  // const modal = document.querySelector('#modal')
  // const hx_modal = modal?.querySelector('#hx-modal')

  // if (modal && hx_modal) {
  //   // HTMX removes the placeholder every time, we need to add it to indicate
  //   // a loading state.
  //   hx_modal.innerHTML = `
  //     <div class='placeholder-scr placeholder-scr--fillscreen'>
  //       <i class='placeholder-scr__icon fad fa-spinner-third fa-spin fa-2x'></i>
  //     </div>
  //   `

  //   const modal = `<div class="tf-modal">
  //     <div class="card card--none card--modal">
  //       <div class="overflow-hidden flex-1"
  //         hx-get="${expression}"
  //         hx-target="this"
  //       >
  //         <div class="placeholder-scr placeholder-scr--fillscreen">
  //           <i class="placeholder-scr__icon fad fa-spinner-third fa-spin fa-2x"></i>
  //         </div>
  //       </div>
  //     </div>
  //   </div>`

  //   hx_modal.setAttribute('hx-get', expression)

  //   // // TODO: decide whether we need this option
  //   // if (event.currentTarget.dataset.modalTarget) {
  //   //   hx_modal.setAttribute('target', event.currentTarget.dataset.modalTarget)
  //   // }

  //   // // TODO: move the modal classes into the fetched template

  //   // modal.className = 'tf-modal'
  //   // if (event.currentTarget.dataset.modalClasses) {
  //   //   modal.classList.add(
  //   //     ...event.currentTarget.dataset.modalClasses.split(' ')
  //   //   )
  //   // }

  //   // // TODO: add modal persistence by parsing expression via regex for int
  //   // if (event.currentTarget.dataset.modalItem) {
  //   //   const params = new URLSearchParams(location.search)
  //   //   params.set('modal_item', event.currentTarget.dataset.modalItem)
  //   //   history.replaceState(
  //   //     {},
  //   //     '',
  //   //     `${location.pathname}?${params.toString()}`
  //   //   )
  //   // }

  //   modal.removeAttribute('hidden')

  //   // TODO: do we need both of these
  //   htmx.process(hx_modal)
  //   hx_modal.dispatchEvent(new CustomEvent('hx-modal-load'))
  // }
}
