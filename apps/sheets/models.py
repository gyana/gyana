import textwrap
from datetime import timedelta

from django.db import models
from django.db.models import F, Q
from model_clone.mixins.clone import CloneMixin

from apps.base.celery import is_bigquery_task_running
from apps.base.models import BaseModel
from apps.integrations.models import Integration

RETRY_LIMIT_DAYS = 3


class SheetsManager(models.Manager):
    def scheduled_for_today_in_project(self, project):
        # stop trying to sync a scheduled sheet after 3 days of failure
        return (
            self.filter(integration__project=project, is_scheduled=True)
            .annotate(last_succeeded=F("failed_at") - F("succeeded_at"))
            .filter(
                Q(succeeded_at__isnull=True)
                | Q(failed_at=None)
                | Q(last_succeeded__lt=timedelta(days=3))
            )
        )


class Sheet(CloneMixin, BaseModel):

    integration = models.OneToOneField(Integration, on_delete=models.CASCADE)

    url = models.URLField()
    cell_range = models.CharField(max_length=64, null=True, blank=True)
    # essentially the version of the file that was synced
    drive_file_last_modified_at_sync = models.DateTimeField(null=True)

    # track the celery task
    sync_task_id = models.UUIDField(null=True)
    sync_started = models.DateTimeField(null=True)

    # automatically sync metadata from google drive
    drive_modified_date = models.DateTimeField(null=True)

    is_scheduled = models.BooleanField(default=False)
    succeeded_at = models.DateTimeField(null=True)
    failed_at = models.DateTimeField(null=True)

    objects = SheetsManager()

    @property
    def is_syncing(self):
        return is_bigquery_task_running(self.sync_task_id, self.sync_started)

    @property
    def table_id(self):
        return f"sheet_{self.id:09}"

    def create_integration(self, title, created_by, project):
        # maximum Google Drive name length is 32767
        name = textwrap.shorten(title, width=255, placeholder="...")
        integration = Integration.objects.create(
            project=project,
            kind=Integration.Kind.SHEET,
            name=name,
            created_by=created_by,
        )
        self.integration = integration

    def sync_updates_from_drive(self):
        from apps.sheets.sheets import get_last_modified_from_drive_file

        self.drive_modified_date = get_last_modified_from_drive_file(self)
        # avoid a race condition with the sync task
        self.save(update_fields=["drive_modified_date"])

    @property
    def up_to_date(self):
        return self.drive_modified_date == self.drive_file_last_modified_at_sync
