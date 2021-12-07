from django.db import models
from django_celery_results.models import TaskResult

from apps.base.models import BaseModel


class Run(BaseModel):
    task_id = models.UUIDField()
    result = models.OneToOneField(TaskResult, null=True, on_delete=models.SET_NULL)
