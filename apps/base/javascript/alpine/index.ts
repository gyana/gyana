import tooltip from './tooltip'
import popover from './popover'

document.addEventListener('alpine:init', () => {
  Alpine.directive('tooltip', tooltip)
  Alpine.data('popover', popover)
})
