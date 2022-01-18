from django.db import models
from django.db.models import Max
from django.urls import reverse
from model_clone import CloneMixin

from apps.base.models import BaseModel
from apps.base.tables import ICONS
from apps.projects.models import Project
from apps.runs.models import JobRun
from apps.tables.models import Table


class Workflow(CloneMixin, BaseModel):
    _clone_excluded_m2m_fields = ["runs"]
    _clone_excluded_o2o_fields = ["last_success_run", "latest_run"]

    class State(models.TextChoices):
        INCOMPLETE = "incomplete", "Incomplete"
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        FAILED = "failed", "Failed"
        SUCCESS = "success", "Success"

    name = models.CharField(max_length=255, default="Untitled")
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    state = models.CharField(
        max_length=16, choices=State.choices, default=State.INCOMPLETE
    )
    last_success_run = models.OneToOneField(
        "runs.JobRun",
        null=True,
        on_delete=models.SET_NULL,
        related_name="workflow_last_success_run_for",
    )
    data_updated = models.DateTimeField(
        auto_now_add=True,
    )
    is_scheduled = models.BooleanField(default=False)

    STATE_TO_ICON = {
        State.INCOMPLETE: ICONS["warning"],
        State.PENDING: ICONS["pending"],
        State.RUNNING: ICONS["loading"],
        State.FAILED: ICONS["error"],
        State.SUCCESS: ICONS["success"],
    }

    STATE_TO_MESSAGE = {
        State.INCOMPLETE: "Workflow setup is incomplete",
        State.PENDING: "Workflow is pending",
        State.RUNNING: "Workflow is currently running",
        State.FAILED: "One of the nodes in this workflow failed",
        State.SUCCESS: "Workflow ran successfully and is up to date",
    }

    RUN_STATE_TO_WORKFLOW_STATE = {
        JobRun.State.PENDING: State.PENDING,
        JobRun.State.RUNNING: State.RUNNING,
        JobRun.State.FAILED: State.FAILED,
        JobRun.State.SUCCESS: State.SUCCESS,
    }

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project_workflows:detail", args=(self.project.id, self.id))

    @property
    def state_icon(self):
        if self.out_of_date:
            return ICONS["warning"]
        return self.STATE_TO_ICON[self.state]

    @property
    def state_text(self):
        if self.out_of_date:
            return "Workflow has been updated since it's last run"
        return self.STATE_TO_MESSAGE[self.state]

    @property
    def latest_run(self):
        return self.runs.order_by("-created").first()

    @property
    def failed(self):
        return self.nodes.exclude(error__isnull=True).exists()

    @property
    def errors(self):
        return {node.id: node.error for node in self.nodes.exclude(error__isnull=True)}

    @property
    def input_tables_fk(self):
        return [
            node.input_table.id
            for node in self.input_nodes.filter(input_table__isnull=False)
        ]

    @property
    def input_tables(self):
        return [
            node.input_table
            for node in self.input_nodes.filter(input_table__isnull=False)
        ]

    @property
    def input_nodes(self):
        from apps.nodes.models import Node

        return self.nodes.filter(kind=Node.Kind.INPUT)

    @property
    def output_nodes(self):
        from apps.nodes.models import Node

        return self.nodes.filter(kind=Node.Kind.OUTPUT)

    @property
    def out_of_date(self):
        if not self.last_success_run:
            return True

        latest_input_updated = Table.objects.filter(
            input_nodes__workflow=self
        ).aggregate(data_updated=Max("data_updated"))["data_updated"]

        if not latest_input_updated:
            return True

        return self.last_success_run.started_at < max(
            self.data_updated, latest_input_updated
        )

    def update_state_from_latest_run(self):
        self.state = (
            self.State.INCOMPLETE
            if not self.latest_run
            else self.RUN_STATE_TO_WORKFLOW_STATE[self.latest_run.state]
        )
        self.last_success_run = (
            self.runs.filter(state=JobRun.State.SUCCESS).order_by("-created").first()
        )
        self.save(update_fields=["state", "last_success_run"])
