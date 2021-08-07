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
            "enable_sync_emails",
        ]
        widgets = {
            "kind": HiddenInput(),
            "project": HiddenInput(),
        }

    service = forms.CharField(required=False, max_length=255, widget=HiddenInput())

    def save(self, commit=True):
        instance = super().save(commit)

        connector = Connector(
            integration=instance, service=self.cleaned_data["service"]
        )
        connector.save()

        return instance
