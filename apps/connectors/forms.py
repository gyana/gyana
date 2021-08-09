from apps.connectors.utils import get_services
from apps.integrations.models import Integration
from django import forms
from django.db import transaction
from django.forms.widgets import HiddenInput

from .models import Connector


class FivetranForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = [
            "kind",
            "project",
        ]
        widgets = {
            "kind": HiddenInput(),
            "project": HiddenInput(),
        }

    service = forms.CharField(required=False, max_length=255, widget=HiddenInput())

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.name = get_services()[self.cleaned_data["service"]]["name"]

        connector = Connector(
            integration=instance, service=self.cleaned_data["service"]
        )

        if commit:
            with transaction.atomic():
                instance.save()
                connector.save()
                self.save_m2m()

        return instance
