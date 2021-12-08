from celery import states
from django.db import models
from django_celery_results.models import TaskResult

from apps.base.models import BaseModel
from apps.base.table import ICONS


class Run(BaseModel):
    class Source(models.TextChoices):
        INTEGRATION = "integration", "Integration"
        WORKFLOW = "workflow", "Workflow"

    class State(models.TextChoices):
        RUNNING = "running", "Running"
        FAILED = "failed", "Failed"
        SUCCESS = "success", "Success"

    task_id = models.UUIDField()
    result = models.OneToOneField(TaskResult, null=True, on_delete=models.SET_NULL)
    source = models.CharField(max_length=16, choices=Source.choices)
    integration = models.ForeignKey(
        "integrations.Integration", null=True, on_delete=models.CASCADE
    )
    workflow = models.ForeignKey(
        "workflows.Workflow", null=True, on_delete=models.CASCADE
    )

    STATE_TO_ICON = {
        State.RUNNING: ICONS["loading"],
        State.FAILED: ICONS["error"],
        State.SUCCESS: ICONS["success"],
    }

    STATE_TO_MESSAGE = {
        State.RUNNING: "Running",
        State.FAILED: "Failed",
        State.SUCCESS: "Success",
    }

    @property
    def source_obj(self):
        return getattr(self, self.source)

    @property
    def state_icon(self):
        return self.STATE_TO_ICON[self.state]

    @property
    def state_text(self):
        return self.STATE_TO_MESSAGE[self.state]

    @property
    def duration(self):
        if self.result:
            return self.result.date_done - self.created

    @property
    def state(self):
        if not self.result or self.result.status in states.UNREADY_STATES:
            return Run.State.RUNNING
        if self.result.status in states.EXCEPTION_STATES:
            return Run.State.FAILED
        return Run.State.SUCCESS
