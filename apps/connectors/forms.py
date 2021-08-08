from apps.integrations.models import Integration
from django import forms
from django.forms.widgets import HiddenInput

from .models import Connector


class FivetranForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = [
            "name",
            "kind",
            "project",
        ]
        widgets = {
            "kind": HiddenInput(),
            "project": HiddenInput(),
        }

    service = forms.CharField(required=False, max_length=255, widget=HiddenInput())

    def save(self, commit=True):
        # saved automatically by parent
        Connector(integration=self.instance, service=self.cleaned_data["service"])

        return super().save(commit)
