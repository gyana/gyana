from datetime import timedelta
from itertools import chain

from apps.base.models import BaseModel
from apps.connectors.config import get_services
from apps.dashboards.models import Dashboard
from apps.projects.models import Project
from apps.users.models import CustomUser
from apps.workflows.models import Workflow
from django.db import models
from django.urls import reverse
from django.utils import timezone
from model_clone.mixins.clone import CloneMixin

PENDING_DELETE_AFTER_DAYS = 7


class IntegrationsManager(models.Manager):
    def pending(self):
        return self.exclude(connector__fivetran_authorized=False).filter(ready=False)

    def ready(self):
        return self.exclude(connector__fivetran_authorized=False).filter(ready=True)

    def broken(self):
        return self.ready().filter(
            kind=Integration.Kind.CONNECTOR,
            connector__fivetran_succeeded_at__lt=timezone.now()
            - timezone.timedelta(hours=24),
        )

    def needs_attention(self):
        return self.pending().exclude(state=Integration.State.LOAD)

    def loading(self):
        return self.pending().filter(state=Integration.State.LOAD)

    def connectors(self):
        return self.ready().filter(kind=Integration.Kind.CONNECTOR)

    def sheets(self):
        return self.ready().filter(kind=Integration.Kind.SHEET)

    def uploads(self):
        return self.ready().filter(kind=Integration.Kind.UPLOAD)

    def pending_should_be_deleted(self):
        return self.pending().filter(
            created__lt=timezone.now() - timedelta(days=PENDING_DELETE_AFTER_DAYS)
        )


class Integration(CloneMixin, BaseModel):
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

    objects = IntegrationsManager()

    _clone_m2o_or_o2m_fields = ["connector_set", "table_set"]
    _clone_o2o_fields = ["sheet", "upload"]

    def __str__(self):
        return self.name

    @property
    def source_obj(self):
        return getattr(self, self.kind)

    @property
    def num_rows(self):
        return (
            self.table_set.all().aggregate(models.Sum("num_rows"))["num_rows__sum"] or 0
        )

    @property
    def last_synced(self):
        return getattr(self, self.kind).last_synced

    @property
    def pending_deletion(self):
        return self.created + timedelta(days=PENDING_DELETE_AFTER_DAYS)

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
        return list(chain(self.used_in_workflows, self.used_in_dashboards))

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

    def get_table_by_pk_safe(self, table_pk):
        from apps.tables.models import Table

        if table_pk is None:
            return self.table_set.first()
        try:
            return self.table_set.get(pk=table_pk)
        except (Table.DoesNotExist, ValueError):
            return self.table_set.first()
