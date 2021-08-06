from apps.connectors.forms import FivetranForm
from apps.sheets.forms import GoogleSheetsForm
from apps.uploads.forms import CSVForm
from django import forms

from .models import Integration


class IntegrationForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name"]


FORM_CLASS_MAP = {
    Integration.Kind.FIVETRAN: FivetranForm,
    Integration.Kind.CSV: CSVForm,
    Integration.Kind.GOOGLE_SHEETS: GoogleSheetsForm,
}
