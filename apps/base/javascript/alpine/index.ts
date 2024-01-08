import tooltip from './tooltip'
import popover from './popover'

const formset = (el, { Alpine }) => {
  return Array.from(el.querySelectorAll('.formset-wrapper')).map((child) => child._x_dataStack).filter(child => child !== undefined).map(child => Alpine.mergeProxies(child))
}

document.addEventListener('alpine:init', () => {
  Alpine.directive('tooltip', tooltip)
  Alpine.data('popover', popover)
  // https://github.com/ryangjchandler/alpine-parent
  Alpine.magic('parent', (el, { Alpine }) => {
      return Alpine.mergeProxies(
          Alpine.closestDataStack(el).slice(1),
      )
  })
  Alpine.magic('formset', formset)
})
