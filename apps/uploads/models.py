import celery
from apps.base.clients import BIGQUERY_JOB_LIMIT
from apps.base.models import BaseModel
from apps.integrations.models import Integration
from apps.projects.models import Project
from apps.users.models import CustomUser
from django.db import models
from django.utils import timezone


class Upload(BaseModel):

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    integration = models.OneToOneField(Integration, on_delete=models.CASCADE, null=True)

    file_gcs_path = models.TextField()
    file_name = models.CharField(max_length=255, null=True)

    external_table_sync_task_id = models.UUIDField(null=True)
    external_table_sync_started = models.DateTimeField(null=True)
    last_synced = models.DateTimeField(null=True)
    created_by = models.ForeignKey(CustomUser, null=True, on_delete=models.SET_NULL)

    @property
    def is_syncing(self):
        if self.external_table_sync_task_id is None:
            return False

        # Celery PENDING does not distinguish pending versus tasks auto-cleared after 24 hours
        # https://stackoverflow.com/a/38267978/15425660
        # BigQuery jobs cannot last longer than 6 hours
        # PROGRESS is a custom state from celery-progress
        result = celery.result.AsyncResult(str(self.external_table_sync_task_id))
        elapsed_time = timezone.now() - self.external_table_sync_started

        return (
            result.status in ("PENDING", "PROGRESS")
            and elapsed_time.total_seconds() < BIGQUERY_JOB_LIMIT
        )
