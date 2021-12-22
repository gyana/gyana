from django import forms
from django.forms.widgets import HiddenInput
from django.utils.html import mark_safe

from apps.base.account import is_scheduled_paid_only
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
        is_scheduled_paid_only(self.fields["is_scheduled"], self.instance.project)

    def post_save(self, instance):
        instance.project.update_schedule()
