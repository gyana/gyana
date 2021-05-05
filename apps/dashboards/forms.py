from django import forms
from django.forms.widgets import HiddenInput

from .models import Dashboard


class DashboardForm(forms.ModelForm):
    class Meta:
        model = Dashboard
        fields = ["name", "project"]
        widgets = {"project": HiddenInput()}
