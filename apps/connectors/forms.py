from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import CheckboxInput, HiddenInput
from django.utils.html import mark_safe
from honeybadger import honeybadger

from apps.base import clients
from apps.base.forms import BaseModelForm, LiveFormsetMixin, LiveUpdateForm
from apps.connectors.fivetran.services.facebook_ads import BASIC_REPORTS
from apps.customreports.models import FacebookAdsCustomReport

from .fivetran.client import FivetranClientError
from .fivetran.config import ServiceTypeEnum
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
            data = clients.fivetran().create(
                self._service,
                self._project.team.id,
                self._project.next_sync_time_utc_string,
            )
        except FivetranClientError as e:
            raise ValidationError(str(e))

        self._data = data

    def pre_save(self, instance):
        instance.update_kwargs_from_fivetran(self._data)
        instance.create_integration(instance.conf.name, self._created_by, self._project)


class ConnectorUpdateForm(LiveFormsetMixin, LiveUpdateForm):
    class Meta:
        model = Connector
        fields = ["setup_mode", "basic_reports"]
        help_texts = {
            "setup_mode": mark_safe(
                "Use <strong>Basic</strong> to get started, and <strong>Advanced</strong> to build custom reports and sync account data"
            )
        }

    def __init__(self, *args, **kwargs):

        self._is_alpha = kwargs.pop("is_alpha")
        super().__init__(*args, **kwargs)
        self._is_alpha = self._is_alpha and self.instance.service == "facebook_ads"

        if not self.is_basic:
            for schema in self.instance.schema_obj.schemas:

                schema_field = f"{schema.name_in_destination}_schema"
                tables_field = f"{schema.name_in_destination}_tables"

                schema_widget = (
                    CheckboxInput()
                    if self.instance.conf.service_type == ServiceTypeEnum.DATABASE
                    else HiddenInput()
                )
                table_widget = ConnectorSchemaMultiSelect
                # disabled fields that cannot be patched
                table_widget._schema_dict = {
                    t.name_in_destination: t for t in schema.tables
                }

                self.fields[schema_field] = forms.BooleanField(
                    initial=schema.enabled,
                    label=schema.display_name,
                    widget=schema_widget,
                    help_text="Include or exclude this schema",
                    required=False,
                )
                self.fields[tables_field] = forms.MultipleChoiceField(
                    choices=[
                        (t.name_in_destination, t.display_name) for t in schema.tables
                    ],
                    widget=ConnectorSchemaMultiSelect,
                    initial=[t.name_in_destination for t in schema.tables if t.enabled],
                    label="Tables",
                    help_text="Select specific tables (you can change this later)",
                    required=False,  # you can uncheck all options
                )

    @property
    def is_basic(self):
        return self.get_live_field("setup_mode") == Connector.SetupMode.BASIC

    def get_live_fields(self):
        if not self._is_alpha:
            return []
        live_fields = ["setup_mode"]
        if self.is_basic:
            live_fields += ["basic_reports"]
        return live_fields

    def post_save(self, instance):
        if self.is_basic:
            for basic_report in instance.basic_reports:
                FacebookAdsCustomReport.objects.get_or_create(
                    connector=instance,
                    table_name=BASIC_REPORTS[basic_report]["custom_table"][
                        "table_name"
                    ],
                    defaults=BASIC_REPORTS[basic_report]["custom_table"],
                )

        cleaned_data = self.clean()
        try:
            schema_obj = instance.schema_obj
            schema_obj.mutate_from_cleaned_data(
                cleaned_data,
                allowlist=instance.basic_reports if self.is_basic else None,
            )
            clients.fivetran().update_schemas(instance, schema_obj.to_dict())
            instance.sync_schema_obj_from_fivetran()

            if self._is_alpha:
                instance.update_fivetran_config()
                if instance.custom_reports and not self.is_basic:
                    clients.fivetran().test(instance)

        except FivetranClientError as e:
            honeybadger.notify(e)
            raise ValidationError(
                "Failed to update, please try again or reach out to support."
            )
