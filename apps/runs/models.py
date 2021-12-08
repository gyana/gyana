import celery
from celery import states
from django.db import models
from django_celery_results.models import TaskResult

from apps.base.models import BaseModel


class Run(BaseModel):
    class Source(models.TextChoices):
        INTEGRATION = "integration", "Integration"
        WORKFLOW = "workflow", "Workflow"

    task_id = models.UUIDField()
    result = models.OneToOneField(TaskResult, null=True, on_delete=models.SET_NULL)
    source = models.CharField(max_length=16, choices=Source.choices)
    integration = models.ForeignKey(
        "integrations.Integration", null=True, on_delete=models.CASCADE
    )
    workflow = models.ForeignKey(
        "workflows.Workflow", null=True, on_delete=models.CASCADE
    )

    @property
    def source_obj(self):
        return getattr(self, self.source)
