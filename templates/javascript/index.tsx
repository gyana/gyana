import SourceSelect from './SourceSelect'
import VisualSelect from './VisualSelect'

// if script is read multiple times don't register component again
customElements.get('select-source') || customElements.define('select-source', SourceSelect)
customElements.get('select-visual') || customElements.define('select-visual', VisualSelect)
