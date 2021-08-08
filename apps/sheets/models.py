import celery
from apps.base.models import BaseModel
from apps.integrations.models import Integration
from apps.projects.models import Project
from django.db import models


class Sheet(BaseModel):

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    integration = models.OneToOneField(Integration, on_delete=models.CASCADE, null=True)

    url = models.URLField()

    cell_range = models.CharField(max_length=64, null=True, blank=True)

    external_table_sync_task_id = models.UUIDField(null=True)
    has_initial_sync = models.BooleanField(default=False)
    last_synced = models.DateTimeField(null=True)

    @property
    def is_syncing(self):
        if self.sheet.external_table_sync_task_id is None:
            return False

        # TODO: Possibly fails for out of date task ids
        # https://stackoverflow.com/a/38267978/15425660
        result = celery.result.AsyncResult(str(self.sheet.external_table_sync_task_id))
        return result.status == "PENDING"
