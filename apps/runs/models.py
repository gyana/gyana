from datetime import timedelta

from celery import states
from django.db import models
from django_celery_results.models import TaskResult

from apps.base.models import BaseModel
from apps.base.table import ICONS


class JobRun(BaseModel):
    class Source(models.TextChoices):
        INTEGRATION = "integration", "Integration"
        WORKFLOW = "workflow", "Workflow"

    class State(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        FAILED = "failed", "Failed"
        SUCCESS = "success", "Success"

    # state is manually updated, or computed from celery result
    state = models.CharField(max_length=8, choices=State.choices)
    started_at = models.DateTimeField(null=True, auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    task_id = models.UUIDField(null=True)
    result = models.OneToOneField(TaskResult, null=True, on_delete=models.SET_NULL)
    source = models.CharField(max_length=16, choices=Source.choices)
    integration = models.ForeignKey(
        "integrations.Integration",
        null=True,
        on_delete=models.CASCADE,
        related_name="runs",
    )
    workflow = models.ForeignKey(
        "workflows.Workflow", null=True, on_delete=models.CASCADE, related_name="runs"
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
        # round to nearest second for display
        if self.result:
            return timedelta(
                seconds=round((self.completed_at - self.started_at).total_seconds())
            )

    def update_run_from_result(self):
        if self.result:
            if self.result.status in states.UNREADY_STATES:
                self.state = JobRun.State.RUNNING
            elif self.result.status in states.EXCEPTION_STATES:
                self.state = JobRun.State.FAILED
            else:
                self.state = JobRun.State.SUCCESS

            self.completed_at = self.result.date_done
            self.save()
