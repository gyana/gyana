from apps.base.models import BaseModel
from apps.integrations.models import Integration
from apps.projects.models import Project
from apps.users.models import CustomUser
from django.db import models


class Upload(BaseModel):

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    integration = models.OneToOneField(Integration, on_delete=models.CASCADE, null=True)

    file_gcs_path = models.TextField()
    file_name = models.CharField(max_length=255, null=True)

    # todo: remove for uploads
    external_table_sync_task_id = models.UUIDField(null=True)
    has_initial_sync = models.BooleanField(default=False)
    last_synced = models.DateTimeField(null=True)
    created_by = models.ForeignKey(CustomUser, null=True, on_delete=models.SET_NULL)
