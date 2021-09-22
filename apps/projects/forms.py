from django import forms
from django.forms.widgets import HiddenInput

from .models import Project, ProjectMembership


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "team", "access"]
        widgets = {"team": HiddenInput()}
