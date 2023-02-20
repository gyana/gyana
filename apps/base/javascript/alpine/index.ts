import Alpine from 'alpinejs'
import clipboard from './clipboard'

window.Alpine = Alpine

Alpine.data('clipboard', clipboard)

Alpine.start()
