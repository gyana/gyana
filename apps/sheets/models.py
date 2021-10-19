import textwrap

from apps.base.celery import is_bigquery_task_running
from apps.base.models import BaseModel
from apps.integrations.models import Integration
from django.db import models
from model_clone.mixins.clone import CloneMixin


class Sheet(CloneMixin, BaseModel):

    integration = models.OneToOneField(Integration, on_delete=models.CASCADE)

    url = models.URLField()
    cell_range = models.CharField(max_length=64, null=True, blank=True)
    # updated prior to each sync
    drive_file_last_modified = models.DateTimeField(null=True)

    # track the celery task
    sync_task_id = models.UUIDField(null=True)
    sync_started = models.DateTimeField(null=True)

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
