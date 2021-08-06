from apps.sheets.forms import GoogleSheetsForm
from apps.uploads.forms import CSVForm
from django import forms
from django.forms.widgets import HiddenInput

from .models import Integration


class IntegrationForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name"]


class FivetranForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name", "service", "kind", "project", "enable_sync_emails"]
        widgets = {
            "kind": HiddenInput(),
            "service": HiddenInput(),
            "project": HiddenInput(),
        }


FORM_CLASS_MAP = {
    Integration.Kind.FIVETRAN: FivetranForm,
    Integration.Kind.CSV: CSVForm,
    Integration.Kind.GOOGLE_SHEETS: GoogleSheetsForm,
}
