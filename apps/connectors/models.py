from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.base.models import BaseModel
from apps.integrations.models import Integration

from .fivetran.config import get_services

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

    def needs_periodic_sync_check(self):

        exclude_succeeded_at_after = timezone.now() - timezone.timedelta(
            hours=FIVETRAN_SYNC_FREQUENCY_HOURS
        )

        # checks fivetran connectors every FIVETRAN_SYNC_FREQUENCY_HOURS seconds for
        # possible updated data, until sync has completed
        # using exclude as need to include where fivetran_succeeded_at is null
        return self.exclude(fivetran_succeeded_at__gt=exclude_succeeded_at_after).all()


class Connector(BaseModel):

    integration = models.OneToOneField(Integration, on_delete=models.CASCADE)

    # service name, see services.yaml
    service = models.TextField(max_length=255)
    # unique identifier for API requests in fivetran
    fivetran_id = models.TextField()
    # schema or schema_prefix for storage in bigquery
    schema = models.TextField()

    # do not display unfinished connectors that are not authorized as pending
    # we delete along with corresponding Fivetran model
    fivetran_authorized = models.BooleanField(default=False)
    # keep track of sync succeeded time from fivetran
    fivetran_succeeded_at = models.DateTimeField(null=True)
    # keep track of when a manual sync is triggered
    fivetran_sync_started = models.DateTimeField(null=True)

    # deprecated: track the celery task
    sync_task_id = models.UUIDField(null=True)
    sync_started = models.DateTimeField(null=True)

    objects = ConnectorsManager()

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
    def is_database(self):
        service_conf = get_services()[self.service]
        return service_conf["requires_schema_prefix"] == "t"

    def update_fivetran_succeeded_at(self, succeeded_at: str):

        # fivetran timestamp string from get response
        # timezone (UTC) information is parsed automatically
        succeeded_at = datetime.strptime(succeeded_at, "%Y-%m-%dT%H:%M:%S.%f%z")

        # ignore outdated information
        if (
            self.fivetran_succeeded_at is not None
            and self.fivetran_succeeded_at > succeeded_at
        ):
            return

        self.fivetran_succeeded_at = succeeded_at
        self.save()

        # update all tables too
        for table in self.integration.table_set.all():
            table.update_data_updated(succeeded_at)
