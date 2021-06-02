import SourceSelect from './SourceSelect'

// if script is read multiple times don't register component again
customElements.get('select-source') || customElements.define('select-source', SourceSelect)
