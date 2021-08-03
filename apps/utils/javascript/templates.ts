import AutocompleteMultiSelect from 'apps/filters/javascript/AutocompleteMultiSelect'
import VisualSelect from 'apps/widgets/javascript/VisualSelect'
import GyWidget from 'apps/widgets/javascript/GyWidget'
import SourceSelect from 'apps/widgets/javascript/SourceSelect'

// if script is read multiple times don't register component again
customElements.get('select-source') || customElements.define('select-source', SourceSelect)
customElements.get('select-visual') || customElements.define('select-visual', VisualSelect)
customElements.get('gy-widget') || customElements.define('gy-widget', GyWidget)
customElements.get('select-autocomplete') ||
  customElements.define('select-autocomplete', AutocompleteMultiSelect)
