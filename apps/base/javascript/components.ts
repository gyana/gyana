import AutocompleteMultiSelect from 'apps/filters/javascript/components/AutocompleteMultiSelect'
import VisualSelect from 'apps/widgets/javascript/components/VisualSelect'
import GyWidget from 'apps/widgets/javascript/components/GyWidget'
import SourceSelect from 'apps/widgets/javascript/components/SourceSelect'

// if script is read multiple times don't register component again
customElements.get('select-source') || customElements.define('select-source', SourceSelect)
customElements.get('select-visual') || customElements.define('select-visual', VisualSelect)
customElements.get('gy-widget') || customElements.define('gy-widget', GyWidget)
customElements.get('select-autocomplete') ||
  customElements.define('select-autocomplete', AutocompleteMultiSelect)
