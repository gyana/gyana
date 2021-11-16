from datetime import datetime

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from apps.base import clients
from apps.base.models import BaseModel
from apps.connectors.fivetran.schema import FivetranSchemaObj
from apps.integrations.models import Integration

from .fivetran.config import ServiceTypeEnum, get_services_obj

FIVETRAN_CHECK_SYNC_TIMEOUT_HOURS = 24
FIVETRAN_SYNC_FREQUENCY_HOURS = 6


class ConnectorsManager(models.Manager):
    def needs_initial_sync_check(self):

        include_sync_started_after = timezone.now() - timezone.timedelta(
            hours=FIVETRAN_CHECK_SYNC_TIMEOUT_HOURS
        )

        # connectors that are currently syncing within 24 hour timeout
        return self.filter(
            integration__state=Integration.State.LOAD,
            fivetran_sync_started__gt=include_sync_started_after,
        )

    def needs_daily_sync_check(self):

        # check connectors where next_daily_sync is in past
        return self.filter(next_daily_sync__lt=timezone.now()).all()


class Connector(BaseModel):
    class ScheduleType(models.TextChoices):
        AUTO = "auto", "Auto"
        MANUAL = "manual", "Manual"

    class SetupState(models.TextChoices):
        BROKEN = "broken", "Broken - the connector setup config is broken"
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

    class UpdateState(models.TextChoices):
        ON_SCHEDULE = (
            "on_schedule",
            "On Schedule - the sync is running smoothly, no delays",
        )
        DELAYED = (
            "delayed",
            "Delayed -  the data is delayed for a longer time than expected for the update",
        )

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

    # internal fields

    integration = models.OneToOneField(Integration, on_delete=models.CASCADE)

    # true after the first authorization, connectors that are never successfully
    # authorized are deleted after 7 days (along with corresponding Fivetran model)
    fivetran_authorized = models.BooleanField(default=False)
    # keep track of when a manual sync is triggered
    fivetran_sync_started = models.DateTimeField(null=True)
    # the value of succeeded_at when tables were last synced from bigquery
    bigquery_succeeded_at = models.DateTimeField(null=True)
    # next daily sync time, determined by team timezone and project daily_sync_time, as UTC
    # not the same time each day in UTC due to daylight savings
    next_daily_sync = models.DateTimeField()

    # automatically sync the fields from fivetran connector to this model
    # https://fivetran.com/docs/rest-api/connectors#fields

    # unique identifier for API requests in fivetran
    fivetran_id = models.TextField()
    group_id = models.TextField()
    # service name, see services.yaml
    service = models.TextField(max_length=255)
    service_version = models.IntegerField()
    # schema or schema_prefix for storage in bigquery
    schema = models.TextField()
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

    objects = ConnectorsManager()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.next_daily_sync = self.integration.project.next_daily_sync

        super().save(*args, **kwargs)

    @property
    def fivetran_dashboard_url(self):
        return f"https://fivetran.com/dashboard/connectors/{self.service}/{self.schema}?requiredGroup={settings.FIVETRAN_GROUP}"

    def create_integration(self, name, created_by, project):
        integration = Integration.objects.create(
            project=project,
            kind=Integration.Kind.CONNECTOR,
            name=name,
            created_by=created_by,
        )
        self.integration = integration

    @property
    def conf(self):
        return get_services_obj()[self.service]

    @property
    def schema_obj(self):
        return FivetranSchemaObj(
            self.schema_config, self.conf.service_type, self.schema
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

    @property
    def daily_schedule_check_completed(self):

        has_started = timezone.now() > self.next_daily_sync
        not_connected = self.setup_state != self.SetupState.CONNECTED
        paused = self.sync_state == self.SyncState.PAUSED
        succeeded = (
            self.succeeded_at is not None and self.succeeded_at > self.next_daily_sync
        )
        failed = self.failed_at is not None and self.failed_at > self.next_daily_sync

        return has_started and (not_connected or paused or succeeded or failed)

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
            return self.schema_obj.all_datasets

        if self.conf.service_type in [
            ServiceTypeEnum.WEBHOOKS,
            ServiceTypeEnum.REPORTING_API,
        ]:
            return {self.schema.split(".")[0]}

        return {self.schema}

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
            "config": data["config"],
            "source_sync_details": data.get("source_sync_details"),
        }

        for key, value in kwargs.items():
            setattr(self, key, value)

    def sync_updates_from_fivetran(self):
        from apps.connectors.sync import end_connector_sync

        data = clients.fivetran().get(self)
        self.update_kwargs_from_fivetran(data)
        self.save()

        if self.schema_config is None:
            self.sync_schema_obj_from_fivetran()

        # fivetran setup is broken or incomplete
        if self.setup_state != self.SetupState.CONNECTED:
            self.integration.state = Integration.State.ERROR
            self.integration.save()

        # a new sync is completed
        if self.succeeded_at != self.bigquery_succeeded_at:
            end_connector_sync(self, not self.integration.table_set.exists())

        if self.daily_schedule_check_completed:
            self.next_daily_sync = self.integration.project.next_daily_sync
            self.save()

    def sync_schema_obj_from_fivetran(self):
        self.schema_config = clients.fivetran().get_schemas(self)
        self.save()

    def update_daily_sync_time_if_changed(self):

        # Either the time is updated by the user, or daylight savings are
        # coming into effect

        daily_sync_time = self.integration.project.next_sync_time_utc_string

        if daily_sync_time != self.daily_sync_time:
            clients.fivetran().update(self, daily_sync_time=daily_sync_time)
            self.sync_updates_from_fivetran()

        if self.next_daily_sync > timezone.now():
            self.next_daily_sync = self.integration.project.next_daily_sync
            self.save()

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
