from django import forms

from apps.base.account import is_scheduled_paid_only
from apps.base.forms import BaseModelForm
from apps.connectors.forms import (
    ConnectorCustomReportsForm,
    ConnectorPrebuiltReportsForm,
    ConnectorSettingsForm,
    ConnectorTablesForm,
)
from apps.customapis.forms import CustomApiUpdateForm
from apps.sheets.forms import SheetUpdateForm
from apps.uploads.forms import UploadUpdateForm

from .models import Integration


class IntegrationForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name"]


TAB_TO_CONNECTOR_FORM_CLASS = {
    "tables": ConnectorTablesForm,
    "prebuilt_reports": ConnectorPrebuiltReportsForm,
    "custom_reports": ConnectorCustomReportsForm,
    "settings": ConnectorSettingsForm,
}

KIND_TO_FORM_CLASS = {
    Integration.Kind.SHEET: SheetUpdateForm,
    Integration.Kind.UPLOAD: UploadUpdateForm,
    Integration.Kind.CUSTOMAPI: CustomApiUpdateForm,
}


def get_kind_to_form_class(kind, tab):
    if kind == Integration.Kind.CONNECTOR:
        return TAB_TO_CONNECTOR_FORM_CLASS[tab]
    return KIND_TO_FORM_CLASS[kind]


class IntegrationUpdateForm(BaseModelForm):
    class Meta:
        model = Integration
        fields = ["is_scheduled"]
        labels = {"is_scheduled": "Automatically sync new data"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        is_scheduled_paid_only(self.fields["is_scheduled"], self.instance.project)

    def post_save(self, instance):
        instance.project.update_schedule()
