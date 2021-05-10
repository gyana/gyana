from django import forms
from django.forms.widgets import HiddenInput

from .models import Integration


class GoogleSheetsForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name", "url", "kind", "project"]
        widgets = {"kind": HiddenInput(), "project": HiddenInput()}
        help_texts = {
            "url": "Needs to be public (TODO: share with service account)",
        }


class CSVForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name", "file", "kind", "project"]
        widgets = {"kind": HiddenInput(), "project": HiddenInput()}


class FivetranForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name", "service", "kind", "project"]
        widgets = {
            "kind": HiddenInput(),
            "service": HiddenInput(),
            "project": HiddenInput(),
        }
