from django import forms
from django.forms.widgets import HiddenInput

from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "team"]
        widgets = {"team": HiddenInput()}
