import AutocompleteMultiSelect from 'apps/filters/javascript/components/AutocompleteMultiSelect'
import VisualSelect from 'apps/widgets/javascript/components/VisualSelect'
import GyWidget from 'apps/widgets/javascript/components/GyWidget'
import SourceSelect from 'apps/widgets/javascript/components/SourceSelect'
import GCSFileUpload from 'apps/uploads/javascript/components/GCSFileUpload'
import ControlWidget from 'apps/controls/javascript/components/ControlWidget'

// if script is read multiple times don't register component again
customElements.get('gy-select-source') || customElements.define('gy-select-source', SourceSelect)
customElements.get('gy-select-visual') || customElements.define('gy-select-visual', VisualSelect)
customElements.get('gy-widget') || customElements.define('gy-widget', GyWidget)
customElements.get('gy-select-autocomplete') ||
  customElements.define('gy-select-autocomplete', AutocompleteMultiSelect)
customElements.get('gcs-file-upload') || customElements.define('gcs-file-upload', GCSFileUpload)
customElements.get('gy-control-widget') || customElements.define('gy-control-widget', ControlWidget)
