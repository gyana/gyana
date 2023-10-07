import tippy from 'tippy.js'

/**
 * Tippy.js powered interactable popover.
 *
 * @link https://atomiks.github.io/tippyjs/
 *
 * @example
 * <div x-data="popover">
 *  <button class="button">Click me!</button>
 *
 *  <template x-ref="body">
 *    <h1>You can use HTML in popovers</h1>
 *  </template>
 * </div>
 */
export default (args) => ({
  init() {
    const { placement, theme, trigger } = args || {}

    console.assert(this.$refs.body, 'Popover components need a body target')

    /** @link https://atomiks.github.io/tippyjs/v6/all-props/ */
    tippy(this.$el, {
      allowHTML: true,
      animation: false,
      appendTo: this.$refs.trigger ? this.$el : () => document.body,
      arrow: false,
      content: this.$refs.body.innerHTML,
      delay: 0,
      interactive: true,
      interactiveBorder: 16,
      maxWidth: 'none',
      placement: placement || 'bottom',
      theme: theme || 'popover',
      trigger: trigger || 'click focus',
      triggerTarget: this.$refs.trigger || this.$el,
      zIndex: 'calc(var(--z-ui) + 1)',
      // Tippy dynamically inserts new HTML for the popper
      onShow: (instance) => htmx.process(instance.popper),
    })
  },

  destroy() {
    // https://atomiks.github.io/tippyjs/v6/tippy-instance/#-property
    if (this.$el._tippy) {
      this.$el._tippy.destroy()
    }
  },
})
