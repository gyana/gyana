from apps.base.account import is_scheduled_help_text
from apps.base.forms import BaseModelForm
from apps.customapis.forms import CustomApiUpdateForm
from apps.sheets.forms import SheetUpdateForm
from apps.uploads.forms import UploadUpdateForm

from .models import Integration

KIND_TO_FORM_CLASS = {
    Integration.Kind.SHEET: SheetUpdateForm,
    Integration.Kind.UPLOAD: UploadUpdateForm,
    Integration.Kind.CUSTOMAPI: CustomApiUpdateForm,
}


class IntegrationNameForm(BaseModelForm):
    class Meta:
        model = Integration
        fields = ["name"]


class IntegrationUpdateForm(BaseModelForm):
    class Meta:
        model = Integration
        fields = ["is_scheduled"]
        labels = {"is_scheduled": "Automatically sync new data"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        is_scheduled_help_text(self.fields["is_scheduled"], self.instance.project)

    def post_save(self, instance):
        instance.project.update_schedule()
