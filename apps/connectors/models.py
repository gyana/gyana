import logging
import uuid
from datetime import datetime

from dirtyfields import DirtyFieldsMixin
from django import forms
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from apps.base import clients
from apps.base.fields import ChoiceArrayField
from apps.base.models import BaseModel
from apps.connectors.clone import update_schema
from apps.connectors.fivetran.schema import FivetranSchemaObj
from apps.connectors.fivetran.services.facebook_ads import (
    BASIC_REPORTS,
    BASIC_REPORTS_CHOICES,
)
from apps.integrations.models import Integration

from .clone import create_fivetran, update_schema
from .fivetran.config import ServiceTypeEnum, get_services_obj

FIVETRAN_CHECK_SYNC_TIMEOUT_HOURS = 24
FIVETRAN_SYNC_FREQUENCY_HOURS = 6


class Connector(DirtyFieldsMixin, BaseModel):
    class ScheduleType(models.TextChoices):
        AUTO = "auto", "Auto"
        MANUAL = "manual", "Manual"

    class SetupState(models.TextChoices):
        BROKEN = "broken", "Broken - the connector setup config is broken"
        NOT_FOUND = "not-found", "Fivetran couldn't find this connector"
        INCOMPLETE = (
            "incomplete",
            "Incomplete - the setup config is incomplete, the setup tests never succeeded",
        )
        CONNECTED = "connected", "Connected - the connector is properly set up"

    class SyncState(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled - the sync is waiting to be run"
        SYNCING = "syncing", "Syncing - the sync is currently running"
        PAUSED = "paused", "Paused - the sync is currently paused"
        RESCHEDULED = (
            "rescheduled",
            "Rescheduled - the sync is waiting until more API calls are available in the source service",
        )
        SUNSET = (
            "sunset",
            "Sunset - this connector is no longer supported and won't sync.",
        )

    class UpdateState(models.TextChoices):
        ON_SCHEDULE = (
            "on_schedule",
            "On Schedule - the sync is running smoothly, no delays",
        )
        DELAYED = (
            "delayed",
            "Delayed -  the data is delayed for a longer time than expected for the update",
        )

    class SetupMode(models.TextChoices):
        BASIC = ("basic", "Basic")
        ADVANCED = ("advanced", "Advanced")

    SETUP_STATE_TO_ICON = {
        SetupState.CONNECTED: "fa fa-check text-green",
        SetupState.INCOMPLETE: "fa fa-exclamation-circle text-orange",
        SetupState.BROKEN: "fa fa-times text-red",
    }

    SYNC_STATE_TO_ICON = {
        SyncState.SCHEDULED: "fa fa-clock",
        SyncState.SYNCING: "fa fa-spinner-third fa-spin",
        SyncState.PAUSED: "fa fa-pause",
        SyncState.RESCHEDULED: "fa fa-history",
    }

    _clone_excluded_fields = [
        # TODO: right now this needs to be falsely copied
        # otherwise the integration won't be shown on the overview page.
        # "fivetran_authorized",
        "fivetran_id",
        "fivetran_sync_started",
        "bigquery_succeeded_at",
        # TODO: should this be added later or do we need to replace the schema during duplication
        "schema_config",
    ]
    _clone_excluded_o2o_fields = ["integration"]
    # internal fields

    integration = models.OneToOneField(Integration, on_delete=models.CASCADE)

    # true after the first authorization, connectors that are never successfully
    # authorized are deleted after 7 days (along with corresponding Fivetran model)
    fivetran_authorized = models.BooleanField(default=False)
    # keep track of when a manual sync is triggered
    fivetran_sync_started = models.DateTimeField(null=True)
    # the value of succeeded_at when tables were last synced from bigquery
    bigquery_succeeded_at = models.DateTimeField(null=True)

    # automatically sync the fields from fivetran connector to this model
    # https://fivetran.com/docs/rest-api/connectors#fields

    # unique identifier for API requests in fivetran
    fivetran_id = models.TextField(unique=True, default=uuid.uuid4)
    group_id = models.TextField()
    # service name, see services.yaml
    service = models.TextField(max_length=255)
    service_version = models.IntegerField()
    # schema or schema_prefix for storage in bigquery
    schema = models.TextField(unique=True)
    paused = models.BooleanField()
    pause_after_trial = models.BooleanField()
    connected_by = models.TextField()
    created_at = models.DateTimeField()
    succeeded_at = models.DateTimeField(null=True)
    failed_at = models.DateTimeField(null=True)
    # in minutes, 1440 is daily
    sync_frequency = models.IntegerField()
    # specified in one hour increments starting from 00:00 to 23:00
    daily_sync_time = models.CharField(max_length=6, null=True)
    schedule_type = models.CharField(max_length=8, choices=ScheduleType.choices)
    setup_state = models.CharField(max_length=16, choices=SetupState.choices)
    sync_state = models.CharField(max_length=16, choices=SyncState.choices)
    update_state = models.CharField(max_length=16, choices=UpdateState.choices)
    is_historical_sync = models.BooleanField()
    tasks = models.JSONField()
    warnings = models.JSONField()
    config = models.JSONField()
    source_sync_details = models.JSONField(null=True)
    # https://fivetran.com/docs/rest-api/connectors#retrieveaconnectorschemaconfig
    schema_config = models.JSONField(null=True)

    # deprecated: track the celery task
    sync_task_id = models.UUIDField(null=True)
    sync_started = models.DateTimeField(null=True)

    # reporting connectors
    setup_mode = models.CharField(
        max_length=16, choices=SetupMode.choices, default=SetupMode.ADVANCED
    )
    basic_reports = ChoiceArrayField(
        models.CharField(max_length=32, choices=BASIC_REPORTS_CHOICES), default=list
    )

    @property
    def fivetran_dashboard_url(self):
        return f"https://fivetran.com/dashboard/connectors/{self.service}/{self.schema}?requiredGroup={settings.FIVETRAN_GROUP}"

    def create_integration(self, name, created_by, project):
        integration = Integration.objects.create(
            project=project,
            kind=Integration.Kind.CONNECTOR,
            name=name,
            created_by=created_by,
            is_scheduled=True,
        )
        self.integration = integration

    @property
    def conf(self):
        return get_services_obj()[self.service]

    @property
    def schema_obj(self):
        return FivetranSchemaObj(
            self.schema_config, self.service, self.conf.service_type, self.schema
        )

    @property
    def requires_authorization(self):
        return self.setup_state != self.SetupState.CONNECTED

    @property
    def fivetran_authorization_url(self):
        internal_redirect = reverse(
            "project_integrations_connectors:authorize",
            args=(
                self.integration.project.id,
                self.id,
            ),
        )

        return clients.fivetran().get_authorize_url(
            self,
            f"{settings.EXTERNAL_URL}{internal_redirect}",
        )

    @cached_property
    def actual_bq_ids(self):
        from apps.connectors.bigquery import get_bq_tables_for_connector

        bq_tables = get_bq_tables_for_connector(self)
        return {f"{t.dataset_id}.{t.table_id}" for t in bq_tables}

    @property
    def synced_bq_ids(self):
        return {table.bq_id for table in self.integration.table_set.all()}

    @property
    def can_skip_resync(self):
        # it is possible to skip a resync if no new tables are added and the
        # connector uses a known schema object (api_cloud and databases)
        # this enables users to deselect tables fast
        return (
            self.conf.service_uses_schema
            and len(self.schema_obj.enabled_bq_ids - self.synced_bq_ids) == 0
        )

    def _parse_fivetran_timestamp(self, timestamp):
        if timestamp is not None:
            return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f%z")

    @property
    def synced_datasets(self):
        return set(self.integration.table_set.values("bq_dataset").distinct())

    @property
    def fivetran_datasets(self):

        # all the datasets derived from the fivetran schema and schema_config information

        if self.conf.service_type == ServiceTypeEnum.DATABASE:
            if self.schema_config is None:
                return set()
            return self.schema_obj.all_datasets

        if self.conf.service_type in [
            ServiceTypeEnum.WEBHOOKS,
            ServiceTypeEnum.REPORTING_API,
        ]:
            return {self.schema.split(".")[0]}

        return {self.schema}

    @property
    def bq_dataset_prefix(self):
        # Webhooks and Report APIs append the table name to the fivetran schema
        if self.conf.service_type in [
            ServiceTypeEnum.WEBHOOKS,
            ServiceTypeEnum.REPORTING_API,
        ]:
            return self.schema.split(".")[0]

        return self.schema

    def update_kwargs_from_fivetran(self, data):
        status = data["status"]

        kwargs = {
            "fivetran_id": data["id"],
            "group_id": data["group_id"],
            "service": data["service"],
            "service_version": data["service_version"],
            "schema": data["schema"],
            "paused": data["paused"],
            "pause_after_trial": data["pause_after_trial"],
            "connected_by": data["connected_by"],
            "created_at": self._parse_fivetran_timestamp(data["created_at"]),
            "succeeded_at": self._parse_fivetran_timestamp(data["succeeded_at"]),
            "failed_at": self._parse_fivetran_timestamp(data["failed_at"]),
            "sync_frequency": data["sync_frequency"],
            "daily_sync_time": data.get("daily_sync_time"),
            "schedule_type": data["schedule_type"],
            "setup_state": status["setup_state"],
            "sync_state": status["sync_state"],
            "update_state": status["update_state"],
            "is_historical_sync": status["is_historical_sync"],
            "tasks": status["tasks"],
            "warnings": status["warnings"],
            "source_sync_details": data.get("source_sync_details"),
        }

        for key, value in kwargs.items():
            setattr(self, key, value)

        # only available for individual connector get (not group list)
        if "config" in data and data["config"] is not None:
            self.config = data["config"]

    @staticmethod
    def sync_all_updates_from_fivetran():

        # until Fivetran implements webhooks, the most reliable syncing method
        # is to list all connectors via /groups/{{ group_id }}/connectors and
        # sync changes locally every 10 minutes

        connectors = Connector.objects.all()
        connectors_dict = {c.fivetran_id: c for c in connectors}

        for data in clients.fivetran().list():
            # ignore orphaned connectors
            if data["id"] in connectors_dict:
                connector = connectors_dict[data["id"]]
                connector.sync_updates_from_fivetran(data)

    def sync_updates_from_fivetran(self, data=None):
        from apps.connectors.fivetran.client import FivetranConnectorNotFound
        from apps.connectors.sync import end_connector_sync

        client = clients.fivetran()
        try:
            data = data or client.get(self)
        except FivetranConnectorNotFound as err:
            # It's not clear how this can happen but it happens
            self.integration.state = Integration.State.ERROR
            self.integration.save()
            self.setup_state = self.SetupState.NOT_FOUND
            self.save()
            logging.error(err, exc_info=err)
            return

        if (
            data["succeeded_at"]
            and (
                timezone.now()
                - datetime.fromisoformat(data["succeeded_at"].replace("Z", "+00:00"))
            ).days
            > 7
        ):
            client.update(self, paused=True)
            data["paused"] = True
            self.paused = True
            self.sync_state = self.SyncState.PAUSED

        if self.sync_state != self.SyncState.SUNSET:
            self.update_kwargs_from_fivetran(data)

        # update fivetran sync time if user has updated timezone/daily sync time
        # or daylight savings time is going in/out tomorrow
        self.daily_sync_time = self.integration.project.next_sync_time_utc_string

        # fivetran setup is broken or incomplete
        if self.setup_state != self.SetupState.CONNECTED:
            self.integration.state = Integration.State.ERROR
            self.integration.save()

        # a new sync is completed
        if self.succeeded_at != self.bigquery_succeeded_at:
            if self.schema_config is None:
                self.sync_schema_obj_from_fivetran()
            end_connector_sync(self, not self.integration.table_set.exists())

        if self.is_dirty():
            if "daily_sync_time" in self.get_dirty_fields():
                clients.fivetran().update(self, daily_sync_time=self.daily_sync_time)
            self.save()

    def sync_schema_obj_from_fivetran(self):
        from apps.connectors.fivetran.client import FivetranClientError

        try:
            self.schema_config = clients.fivetran().get_schemas(self)
            self.save()
        except FivetranClientError:
            # certain connectors fail to return schema objects
            pass

    @property
    def custom_reports(self):
        if self.setup_mode == self.SetupMode.BASIC:
            return [BASIC_REPORTS[r]["custom_table"] for r in self.basic_reports]
        return [
            forms.model_to_dict(obj) for obj in self.facebookadscustomreport_set.all()
        ]

    def update_fivetran_config(self):
        clients.fivetran().update(
            self, config={**self.config, "custom_tables": self.custom_reports}
        )

    @property
    def setup_state_icon(self):
        return self.SETUP_STATE_TO_ICON[self.setup_state]

    @property
    def sync_state_icon(self):
        return self.SYNC_STATE_TO_ICON[self.sync_state]

    @property
    def latest_sync_completed(self):
        return (
            self.succeeded_at is not None
            and self.succeeded_at > self.fivetran_sync_started
        )

    @property
    def latest_sync_failed(self):
        return (
            self.failed_at is not None and self.failed_at > self.fivetran_sync_started
        )

    @property
    def latest_sync_validated(self):
        return self.succeeded_at == self.bigquery_succeeded_at

    def make_clone(self, attrs=None, sub_clone=False, using=None):
        attrs = update_schema(attrs, self)
        clone = super().make_clone(attrs=attrs, sub_clone=sub_clone, using=using)
        create_fivetran(self, clone)

        return clone
