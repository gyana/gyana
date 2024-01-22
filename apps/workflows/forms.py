from django.forms.widgets import HiddenInput

from apps.base.account import is_scheduled_help_text
from apps.base.forms import ModelForm

from .models import Workflow


class WorkflowFormCreate(ModelForm):
    class Meta:
        model = Workflow
        fields = ["project"]
        widgets = {"project": HiddenInput()}


class WorkflowNameForm(ModelForm):
    class Meta:
        model = Workflow
        fields = ["name"]


class WorkflowSettingsForm(ModelForm):
    class Meta:
        model = Workflow
        fields = ["is_scheduled"]
        labels = {"is_scheduled": "Automatically run this workflow on a daily schedule"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        is_scheduled_help_text(self.fields["is_scheduled"], self.instance.project)

    def post_save(self, instance):
        instance.project.update_schedule()
