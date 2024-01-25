import tooltip from './tooltip'
import popover from './popover'
import modal from './modal'

document.addEventListener('alpine:init', () => {
  Alpine.directive('tooltip', tooltip)
  Alpine.data('popover', popover)
  Alpine.directive('modal', modal)
})
