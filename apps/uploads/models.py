from apps.base.models import BaseModel
from apps.integrations.models import Integration
from django.db import models


class Upload(BaseModel):

    integration = models.OneToOneField(Integration, on_delete=models.CASCADE)

    file = models.TextField()

    # todo: remove for uploads
    external_table_sync_task_id = models.UUIDField(null=True)
    has_initial_sync = models.BooleanField(default=False)
    last_synced = models.DateTimeField(null=True)
