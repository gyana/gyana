from apps.base.clients import fivetran_client
from apps.connectors.config import get_services
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


class ConnectorUpdateForm(forms.ModelForm):
    class Meta:
        model = Connector
        fields = []

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        schemas = fivetran_client().get_schema(self.instance.fivetran_id)

        is_database = (
            get_services()[self.instance.service]["requires_schema_prefix"] == "t"
        )

        for schema, schema_config in schemas.items():
            tables = schema_config["tables"]

            self.fields[f"{schema}_schema"] = forms.BooleanField(
                initial=schema_config["enabled"],
                label=schema.replace("_", " ").title(),
                widget=CheckboxInput() if is_database else HiddenInput(),
            )
            self.fields[f"{schema}_tables"] = forms.MultipleChoiceField(
                choices=[(t, t.replace("_", " ").title()) for t in tables],
                widget=MultiSelect,
                initial=[t for t in tables if tables[t]["enabled"]],
                label="Tables",
            )

    def clean(self):
        cleaned_data = super().clean()

        # reformat data into schema dict via mutation
        schemas = fivetran_client().get_schema(self.instance.fivetran_id)

        for schema, schema_config in schemas.items():
            schema_config["enabled"] = f"{schema}_schema" in cleaned_data
            for table, table_config in schema_config["tables"].items():
                table_config["enabled"] = table in cleaned_data[f"{schema}_tables"]

        # update fivetran and throw validation failure on errors
        fivetran_client().update_schema(self.instance.fivetran_id, schemas)
