import AutocompleteMultiSelect from 'apps/filters/javascript/components/AutocompleteMultiSelect'
import GyWidget from 'apps/widgets/javascript/components/GyWidget'
import GCSFileUpload from 'apps/uploads/javascript/components/GCSFileUpload'

// if script is read multiple times don't register component again
customElements.get('gy-widget') || customElements.define('gy-widget', GyWidget)
customElements.get('gy-select-autocomplete') ||
  customElements.define('gy-select-autocomplete', AutocompleteMultiSelect)
customElements.get('gcs-file-upload') ||
  customElements.define('gcs-file-upload', GCSFileUpload)
