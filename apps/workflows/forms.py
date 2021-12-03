from django import forms
from django.forms.widgets import HiddenInput

from apps.base.forms import BaseModelForm

from .models import Workflow


class WorkflowFormCreate(forms.ModelForm):
    class Meta:
        model = Workflow
        fields = ["project"]
        widgets = {"project": HiddenInput()}


class WorkflowForm(forms.ModelForm):
    class Meta:
        model = Workflow
        fields = ["name"]


class WorkflowSettingsForm(BaseModelForm):
    class Meta:
        model = Workflow
        fields = ["is_scheduled"]
        labels = {"is_scheduled": "Automatically run this workflow on a daily schedule"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.instance.project
        help_text = f"Daily at {project.daily_schedule_time} in {project.team.timezone}"
        self.fields["is_scheduled"].help_text = help_text

    def post_save(self, instance):
        instance.project.update_schedule()
