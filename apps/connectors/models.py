from apps.projects.models import Project
from django.db import models


class Connector(models.Model):

    name = models.CharField(max_length=255)

    service = models.TextField(max_length=255)
    fivetran_id = models.TextField(null=True)
    schema = models.TextField(null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    fivetran_authorized = models.BooleanField(default=False)
    fivetran_poll_historical_sync_task_id = models.UUIDField(null=True)
    historical_sync_complete = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self) -> str:
        return self.name
