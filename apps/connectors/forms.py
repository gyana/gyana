from apps.base.clients import fivetran_client
from apps.connectors.fivetran import FivetranClient
from apps.connectors.utils import get_services
from apps.integrations.models import Integration
from django import forms
from django.core.exceptions import ValidationError
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

    def clean(self):

        # try to create fivetran entity
        res = fivetran_client().create(self._service, self._project.team.id)

        if not res["success"]:
            raise ValidationError(res["message"])

        self._fivetran_id = res["data"]["fivetran_id"]
        self._schema = res["data"]["schema"]

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.service = self._service
        instance.fivetran_id = self._fivetran_id
        instance.schema = self._schema

        name = get_services()[self._service]["name"]

        integration = Integration(
            project=self._project,
            kind=Integration.Kind.CONNECTOR,
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
