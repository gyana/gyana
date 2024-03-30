import AutocompleteMultiSelect from 'apps/filters/javascript/components/AutocompleteMultiSelect'
import GyWidget from 'apps/widgets/javascript/components/GyWidget'

// if script is read multiple times don't register component again
customElements.get('gy-widget') || customElements.define('gy-widget', GyWidget)
customElements.get('gy-select-autocomplete') ||
  customElements.define('gy-select-autocomplete', AutocompleteMultiSelect)
