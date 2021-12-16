from django import forms

from apps.apis.forms import CustomApiUpdateForm
from apps.connectors.forms import ConnectorSettingsForm, ConnectorUpdateForm
from apps.sheets.forms import SheetSettingsForm, SheetUpdateForm
from apps.uploads.forms import UploadSettingsForm, UploadUpdateForm

from .models import Integration


class IntegrationForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name"]


KIND_TO_FORM_CLASS = {
    Integration.Kind.CONNECTOR: ConnectorUpdateForm,
    Integration.Kind.SHEET: SheetUpdateForm,
    Integration.Kind.UPLOAD: UploadUpdateForm,
    Integration.Kind.CUSTOM_API: CustomApiUpdateForm,
}

KIND_TO_SETTINGS_FORM_CLASS = {
    Integration.Kind.CONNECTOR: ConnectorSettingsForm,
    Integration.Kind.SHEET: SheetSettingsForm,
    Integration.Kind.UPLOAD: UploadSettingsForm,
    Integration.Kind.CUSTOM_API: CustomApiUpdateForm,
}
