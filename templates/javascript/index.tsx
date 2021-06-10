import AutocompleteMultiSelect from './AutocompleteMultiSelect'
import SourceSelect from './SourceSelect'
import VisualSelect from './VisualSelect'
import Rnd from './Rnd'

// if script is read multiple times don't register component again
customElements.get('select-source') || customElements.define('select-source', SourceSelect)
customElements.get('select-visual') || customElements.define('select-visual', VisualSelect)
customElements.get('react-rnd') || customElements.define('react-rnd', Rnd)
customElements.get('select-autocomplete') ||
  customElements.define('select-autocomplete', AutocompleteMultiSelect)
