from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import CheckboxInput, HiddenInput
from honeybadger import honeybadger

from apps.base import clients
from apps.base.forms import BaseModelForm

from .fivetran.client import FivetranClientError
from .fivetran.config import get_services
from .fivetran.schema import update_schema_from_cleaned_data
from .models import Connector
from .widgets import ConnectorSchemaMultiSelect


class ConnectorCreateForm(BaseModelForm):
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
            res = clients.fivetran().create(self._service, self._project.team.id)
        except FivetranClientError as e:
            raise ValidationError(str(e))

        self._fivetran_id = res["fivetran_id"]
        self._schema = res["schema"]

    def pre_save(self, instance):
        instance.service = self._service
        instance.fivetran_id = self._fivetran_id
        instance.schema = self._schema
        instance.create_integration(
            get_services()[self._service]["name"], self._created_by, self._project
        )


class ConnectorUpdateForm(forms.ModelForm):
    class Meta:
        model = Connector
        fields = []

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        schemas = clients.fivetran().get_schemas(self.instance)

        for schema in schemas:

            self.fields[f"{schema.name_in_destination}_schema"] = forms.BooleanField(
                initial=schema.enabled,
                label=schema.display_name,
                widget=CheckboxInput() if self.instance.is_database else HiddenInput(),
                help_text="Include or exclude this schema",
                required=False,
            )
            self.fields[
                f"{schema.name_in_destination}_tables"
            ] = forms.MultipleChoiceField(
                choices=[
                    (t.name_in_destination, t.display_name) for t in schema.tables
                ],
                widget=ConnectorSchemaMultiSelect,
                initial=[t.name_in_destination for t in schema.tables if t.enabled],
                label="Tables",
                help_text="Select specific tables (you can change this later)",
                required=False,  # you can uncheck all options
            )

            # disabled fields that cannot be patched
            self.fields[f"{schema.name_in_destination}_tables"].widget._schema_dict = {
                t.name_in_destination: t for t in schema.tables
            }

    def clean(self):
        cleaned_data = super().clean()
        try:
            update_schema_from_cleaned_data(self.instance, cleaned_data)
        except FivetranClientError as e:
            honeybadger.notify(e)
            raise ValidationError(
                "Failed to update, please try again or reach out to support."
            )
