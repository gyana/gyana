import celery
from apps.base.models import BaseModel
from apps.connectors.utils import get_services
from apps.dashboards.models import Dashboard
from apps.projects.models import Project
from apps.users.models import CustomUser
from apps.workflows.models import Workflow
from django.db import models
from django.urls import reverse


class Integration(BaseModel):
    class Kind(models.TextChoices):
        GOOGLE_SHEETS = "sheets", "Google Sheets"
        CSV = "upload", "Upload"
        FIVETRAN = "connector", "Connector"

    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    kind = models.CharField(max_length=32, choices=Kind.choices)

    # Sync toggle
    enable_sync_emails = models.BooleanField(default=True)

    created_by = models.ForeignKey(CustomUser, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

    @property
    def num_rows(self):
        return self.table_set.all().aggregate(models.Sum("num_rows"))["num_rows__sum"]

    def start_sheets_sync(self):
        from apps.sheets.tasks import run_sheets_sync

        result = run_sheets_sync.delay(self.id)
        self.external_table_sync_task_id = result.task_id

        self.save()

    @property
    def is_syncing(self):
        if self.external_table_sync_task_id is None:
            return False

        # TODO: Possibly fails for out of date task ids
        # https://stackoverflow.com/a/38267978/15425660
        result = celery.result.AsyncResult(str(self.external_table_sync_task_id))
        return result.status == "PENDING"

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
            if self.kind != self.Kind.FIVETRAN
            else get_services()[self.service]["name"]
        )

    def get_table_name(self):
        return f"Integration:{self.name}"

    def get_absolute_url(self):
        return reverse("project_integrations:detail", args=(self.project.id, self.id))

    def icon(self):
        if self.kind == Integration.Kind.FIVETRAN:
            return f"images/integrations/fivetran/{self.service}.svg"
        return f"images/integrations/{self.kind}.svg"
