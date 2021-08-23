from apps.connectors.forms import ConnectorUpdateForm
from apps.sheets.forms import SheetUpdateForm
from apps.uploads.forms import UploadUpdateForm
from django import forms

from .models import Integration


class IntegrationForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name"]


KIND_TO_FORM_CLASS = {
    Integration.Kind.CONNECTOR: ConnectorUpdateForm,
    Integration.Kind.SHEET: SheetUpdateForm,
    Integration.Kind.UPLOAD: UploadUpdateForm,
}
