from apps.base.celery import is_bigquery_task_running
from apps.base.models import BaseModel
from apps.integrations.models import Integration
from django.db import models


class Upload(BaseModel):

    integration = models.OneToOneField(Integration, on_delete=models.CASCADE)

    file_gcs_path = models.TextField()

    # track the celery task
    sync_task_id = models.UUIDField(null=True)
    sync_started = models.DateTimeField(null=True)

    @property
    def is_syncing(self):
        return is_bigquery_task_running(self.sync_task_id, self.sync_started)
