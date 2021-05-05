from django import forms
from django.forms.widgets import HiddenInput

from .models import Dataset


class GoogleSheetsForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ["name", "url", "kind", "project"]
        widgets = {"kind": HiddenInput(), "project": HiddenInput()}
        help_texts = {
            "url": "Needs to be public (TODO: share with service account)",
        }


class CSVForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ["name", "file", "kind", "project"]
        widgets = {"kind": HiddenInput(), "project": HiddenInput()}
