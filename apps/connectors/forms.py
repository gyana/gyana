from apps.connectors.utils import get_services
from apps.integrations.models import Integration
from django import forms
from django.db import transaction

from .models import Connector


class ConnectorCreateForm(forms.ModelForm):
    class Meta:
        model = Connector
        fields = []

    def __init__(self, *args, **kwargs):
        self._project = kwargs.pop("project")
        self._service = kwargs.pop("service")
        self._created_by = kwargs.pop("created_by")

        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.service = self._service

        name = get_services()[self._service]["name"]

        integration = Integration(
            project=self._project,
            kind=Integration.Kind.SHEET,
            name=name,
            created_by=self._created_by,
        )
        instance.integration = integration

        if commit:
            with transaction.atomic():
                integration.save()
                instance.save()
                self.save_m2m()

        return instance
