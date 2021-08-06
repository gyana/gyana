from apps.integrations.models import Integration
from django import forms
from django.forms.widgets import HiddenInput


class FivetranForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name", "service", "kind", "project", "enable_sync_emails"]
        widgets = {
            "kind": HiddenInput(),
            "service": HiddenInput(),
            "project": HiddenInput(),
        }
