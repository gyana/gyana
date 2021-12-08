from datetime import timedelta

from celery import states
from dirtyfields import DirtyFieldsMixin
from django.db import models
from django_celery_results.models import TaskResult

from apps.base.models import BaseModel
from apps.base.table import ICONS


class JobRun(DirtyFieldsMixin, BaseModel):
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
    started_at = models.DateTimeField(null=True)
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

    def save(self, *args, **kwargs):
        dirty = set(self.get_dirty_fields()) & {"state"}
        super().save(*args, **kwargs)
        if dirty:
            self.source_obj.update_state_from_latest_run()

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
        if self.started_at and self.completed_at:
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
