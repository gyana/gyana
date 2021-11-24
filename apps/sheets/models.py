import textwrap

from django.db import models
from django.utils import timezone
from model_clone.mixins.clone import CloneMixin

from apps.base.celery import is_bigquery_task_running
from apps.base.models import BaseModel
from apps.integrations.models import Integration

RETRY_LIMIT_DAYS = 3


class SheetsManager(models.Manager):
    def needs_daily_sync(self):
        return self.filter(is_scheduled=True, next_daily_sync__lt=timezone.now())


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
    # the next time to check for a sync from Google Sheets
    next_daily_sync = models.DateTimeField(null=True)
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

    @property
    def retry_limit_exceeded(self):
        # stop retrying a failed connected after three days of errors
        if self.succeeded_at is None:
            return True
        return (timezone.now() - self.succeeded_at).days > RETRY_LIMIT_DAYS

    def update_next_daily_sync(self):
        if not self.is_scheduled:
            self.next_daily_sync = None
        # if timezone.now() > self.next_daily_sync, wait for the current job
        # to complete, and it will automatically update the next_daily_sync
        elif self.next_daily_sync is None or timezone.now() < self.next_daily_sync:
            self.next_daily_sync = self.integration.project.next_daily_sync
        self.save()
