from django import forms
from waffle import flag_is_active

from apps.base.forms import BaseModelForm
from apps.connectors.forms import ConnectorUpdateForm
from apps.customapis.forms import CustomApiUpdateForm
from apps.sheets.forms import SheetUpdateForm
from apps.uploads.forms import UploadUpdateForm

from .models import Integration


class IntegrationForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name"]


KIND_TO_FORM_CLASS = {
    Integration.Kind.CONNECTOR: ConnectorUpdateForm,
    Integration.Kind.SHEET: SheetUpdateForm,
    Integration.Kind.UPLOAD: UploadUpdateForm,
    Integration.Kind.CUSTOMAPI: CustomApiUpdateForm,
}


class IntegrationUpdateForm(BaseModelForm):
    class Meta:
        model = Integration
        fields = ["is_scheduled"]
        labels = {"is_scheduled": "Automatically sync new data"}

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        super().__init__(*args, **kwargs)
        project = self.instance.project
        help_text = f"Daily at {project.daily_schedule_time} in {project.team.timezone}"
        self.fields["is_scheduled"].help_text = help_text
        if not flag_is_active(request, "beta"):
            self.fields.pop("is_scheduled")

    def post_save(self, instance):
        instance.project.update_schedule()
