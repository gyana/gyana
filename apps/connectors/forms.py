from django import forms
from django.forms.widgets import HiddenInput

from .models import Connector


class ConnectorForm(forms.ModelForm):
    class Meta:
        model = Connector
        fields = ["name", "service", "project"]
        widgets = {"service": HiddenInput(), "project": HiddenInput()}
