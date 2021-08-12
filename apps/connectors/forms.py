from apps.base.clients import fivetran_client
from apps.connectors.config import get_services
from apps.connectors.fivetran import FivetranClientError
from apps.integrations.models import Integration
from apps.nodes.widgets import MultiSelect
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms.widgets import CheckboxInput, HiddenInput

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
        try:
            res = fivetran_client().create(self._service, self._project.team.id)
        except FivetranClientError as e:
            raise ValidationError(str(e))

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


class ConnectorUpdateForm(forms.ModelForm):
    class Meta:
        model = Connector
        fields = []

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        schemas = fivetran_client().get_schemas(self.instance)

        is_database = (
            get_services()[self.instance.service]["requires_schema_prefix"] == "t"
        )

        for schema in schemas:

            self.fields[f"{schema.name_in_destination}_schema"] = forms.BooleanField(
                initial=schema.enabled,
                label=schema.name_in_destination.replace("_", " ").title(),
                widget=CheckboxInput() if is_database else HiddenInput(),
            )
            self.fields[
                f"{schema.name_in_destination}_tables"
            ] = forms.MultipleChoiceField(
                choices=[
                    (
                        t.name_in_destination,
                        t.name_in_destination.replace("_", " ").title(),
                    )
                    for t in schema.tables
                ],
                widget=MultiSelect,
                initial=[t.name_in_destination for t in schema.tables if t.enabled],
                label="Tables",
            )

    def clean(self):
        cleaned_data = super().clean()

        # mutate the schema information based on user input
        schemas = fivetran_client().get_schemas(self.instance)

        for schema in schemas:
            schema.enabled = f"{schema.name_in_destination}_schema" in cleaned_data
            for table in schema.tables:
                # field does not exist if all unchecked
                table.enabled = table in cleaned_data.get(
                    f"{schema.name_in_destination}_tables", []
                )

        # try to update the fivetran schema
        try:
            fivetran_client().update_schemas(self.instance, schemas)
        except FivetranClientError:
            raise ValidationError(
                "Failed to update, please try again or reach out to support."
            )
