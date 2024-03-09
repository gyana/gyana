import tippy from 'tippy.js'

/**
 * Simple Tippy.js alpine wrapper.
 *
 * @link https://atomiks.github.io/tippyjs/
 *
 * @example
 * <p x-tooltip.sidebar="This is the tooltip!"/>
 *
 * @example
 * <p x-tooltip.bottom="This is the tooltip!"/>
 */
export default (el, { modifiers, expression }, { cleanup }) => {
  const modifier = modifiers[0] || 'bottom'
  const placement = modifier === 'sidebar' ? 'right' : modifier

  tippy(el, {
    animation: false,
    content: expression,
    delay: 0,
    // sidebar element hides the tooltip when the sidebar is expanded
    onShow(instance) {
      if (
        modifier === 'sidebar' &&
        document.querySelector('#sidebar-toggle:checked')
      ) {
        return false
      }
    },
    placement,
  })

  cleanup(() => {
    if (el._tippy) {
      el._tippy.destroy()
    }
  })
}
