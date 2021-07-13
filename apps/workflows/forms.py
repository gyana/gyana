from django import forms
from django.forms.widgets import HiddenInput

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
