from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import CheckboxInput, HiddenInput
from honeybadger import honeybadger

from apps.base import clients
from apps.base.forms import BaseModelForm, LiveFormsetMixin
from apps.base.formsets import RequiredInlineFormset
from apps.connectors.fivetran.services import facebook_ads

from .fivetran.client import FivetranClientError
from .fivetran.config import ServiceTypeEnum
from .models import Connector, FacebookAdsCustomReport
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


class ConnectorTablesForm(LiveFormsetMixin, BaseModelForm):
    class Meta:
        model = Connector
        fields = []

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.instance.sync_schema_obj_from_fivetran()

        for schema in self.instance.schema_obj.schemas:

            self.fields[f"{schema.name_in_destination}_schema"] = forms.BooleanField(
                initial=schema.enabled,
                label=schema.display_name,
                widget=CheckboxInput()
                if self.instance.conf.service_type == ServiceTypeEnum.DATABASE
                else HiddenInput(),
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

    def post_save(self, instance):
        cleaned_data = self.clean()
        try:
            schema_obj = instance.schema_obj
            schema_obj.mutate_from_cleaned_data(cleaned_data)
            clients.fivetran().update_schemas(instance, schema_obj.to_dict())
            instance.sync_schema_obj_from_fivetran()

        except FivetranClientError as e:
            honeybadger.notify(e)
            raise ValidationError(
                "Failed to update, please try again or reach out to support."
            )


class ConnectorPrebuiltReportsForm(LiveFormsetMixin, BaseModelForm):
    class Meta:
        model = Connector
        fields = ["prebuilt_reports"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["prebuilt_reports"].choices = zip(
            facebook_ads.PREBUILT_REPORTS, facebook_ads.PREBUILT_REPORTS
        )

    def post_save(self, instance):
        try:
            instance.update_fivetran_config()
            clients.fivetran().test(instance)
        except FivetranClientError as e:
            honeybadger.notify(e)
            raise ValidationError(e)


class ConnectorCustomReportsForm(LiveFormsetMixin, BaseModelForm):
    class Meta:
        model = Connector
        fields = []

    def post_save(self, instance):
        try:
            instance.update_fivetran_config()
            clients.fivetran().test(instance)
        except FivetranClientError as e:
            honeybadger.notify(e)
            raise ValidationError(e)

    def get_live_formsets(self):
        return [FacebookAdCustomReportFormset]


class FacebookAdsCustomReportForm(BaseModelForm):
    class Meta:
        model = FacebookAdsCustomReport
        fields = "__all__"


FacebookAdCustomReportFormset = forms.inlineformset_factory(
    Connector,
    FacebookAdsCustomReport,
    form=FacebookAdsCustomReportForm,
    can_delete=True,
    extra=0,
    formset=RequiredInlineFormset,
)
