import tooltip from './tooltip'

document.addEventListener('alpine:init', () => {
  Alpine.directive('tooltip', tooltip)
})
