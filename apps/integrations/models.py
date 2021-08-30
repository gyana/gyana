from apps.base.models import BaseModel
from apps.connectors.config import get_services
from apps.dashboards.models import Dashboard
from apps.projects.models import Project
from apps.users.models import CustomUser
from apps.workflows.models import Workflow
from django.db import models
from django.urls import reverse


class Integration(BaseModel):
    class Kind(models.TextChoices):
        SHEET = "sheet", "Sheet"
        UPLOAD = "upload", "Upload"
        CONNECTOR = "connector", "Connector"

    class State(models.TextChoices):
        UPDATE = "update", "Update"
        LOAD = "load", "Load"
        ERROR = "error", "Error"
        DONE = "done", "Done"

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    kind = models.CharField(max_length=32, choices=Kind.choices)

    # user editable name, auto-populated in the initial sync
    name = models.CharField(max_length=255)

    state = models.CharField(max_length=16, choices=State.choices, default=State.UPDATE)
    # only "ready" are available for analytics and count towards user rows
    ready = models.BooleanField(default=False)
    created_ready = models.DateTimeField(null=True)
    created_by = models.ForeignKey(CustomUser, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

    @property
    def source_obj(self):
        return getattr(self, self.kind)

    @property
    def num_rows(self):
        return self.table_set.all().aggregate(models.Sum("num_rows"))["num_rows__sum"]

    @property
    def last_synced(self):
        return getattr(self, self.kind).last_synced

    @property
    def used_in_workflows(self):
        return (
            Workflow.objects.filter(nodes__input_table__in=self.table_set.all())
            .distinct()
            .only("name", "project", "created", "updated")
            .annotate(kind=models.Value("Workflow", output_field=models.CharField()))
        )

    @property
    def used_in_dashboards(self):
        return (
            Dashboard.objects.filter(widget__table__in=self.table_set.all())
            .distinct()
            .only("name", "project", "created", "updated")
            .annotate(kind=models.Value("Dashboard", output_field=models.CharField()))
        )

    @property
    def used_in(self):
        return self.used_in_workflows.union(self.used_in_dashboards)

    @property
    def display_kind(self):
        return (
            self.get_kind_display()
            if self.kind != self.Kind.CONNECTOR
            else get_services()[self.connector.service]["name"]
        )

    def get_table_name(self):
        return f"Integration:{self.name}"

    def get_absolute_url(self):
        return reverse("project_integrations:detail", args=(self.project.id, self.id))

    def icon(self):
        if self.kind == Integration.Kind.CONNECTOR:
            return f"images/integrations/fivetran/{get_services()[self.connector.service]['icon_path']}"
        return f"images/integrations/{self.kind}.svg"
