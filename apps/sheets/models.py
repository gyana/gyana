from apps.base.models import BaseModel
from apps.integrations.models import Integration
from django.db import models


class Sheet(BaseModel):

    integration = models.OneToOneField(
        Integration,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    url = models.URLField()

    cell_range = models.CharField(max_length=64, null=True, blank=True)

    external_table_sync_task_id = models.UUIDField(null=True)
    has_initial_sync = models.BooleanField(default=False)
    last_synced = models.DateTimeField(null=True)
