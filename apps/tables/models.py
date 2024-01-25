from itertools import chain

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property

from apps.base.clients import get_engine
from apps.base.models import BaseModel
from apps.projects.models import Project
from apps.tables.clone import create_attrs

from .clone import create_attrs, duplicate_table


class AvailableManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(integration__ready=False)


class Table(BaseModel):
    class Meta:
        unique_together = ["name", "namespace"]
        ordering = ("-created",)

    class Source(models.TextChoices):
        INTEGRATION = "integration", "Integration"
        WORKFLOW_NODE = "workflow_node", "Workflow node"
        INTERMEDIATE_NODE = "intermediate_node", "Intermediate node"
        CACHE_NODE = "cache_node", "Cache node"

    _clone_excluded_o2o_fields = ["workflow_node", "cache_node", "intermediate_node"]
    _clone_excluded_m2o_or_o2m_fields = ["input_nodes", "exports", "widget_set"]

    name = models.CharField(max_length=settings.BIGQUERY_TABLE_NAME_LENGTH)
    namespace = models.CharField(max_length=settings.BIGQUERY_TABLE_NAME_LENGTH)

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    source = models.CharField(max_length=18, choices=Source.choices)
    integration = models.ForeignKey(
        "integrations.Integration", on_delete=models.CASCADE, null=True
    )
    workflow_node = models.OneToOneField(
        "nodes.Node", on_delete=models.CASCADE, null=True
    )
    intermediate_node = models.OneToOneField(
        "nodes.Node",
        on_delete=models.CASCADE,
        null=True,
        related_name="intermediate_table",
    )
    cache_node = models.OneToOneField(
        "nodes.Node",
        on_delete=models.CASCADE,
        null=True,
        related_name="cache_table",
    )

    num_rows = models.IntegerField(default=0)
    data_updated = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    available = AvailableManager()

    copied_from = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return getattr(self, self.source).get_table_name()

    @property
    def fqn(self):
        return f"{self.namespace}.{self.name}"

    @property
    def humanize(self):
        return self.name.replace("_", " ").title()

    @cached_property
    def schema(self):
        return get_engine().get_table(self).schema()

    @property
    def owner_name(self):
        if self.source == self.Source.INTEGRATION:
            return self.integration.name
        return f"{self.workflow_node.workflow.name} - {self.workflow_node.name or 'Untitled'}"

    @property
    def bq_dashboard_url(self):
        return get_engine().get_dashboard_url(self.namespace, self.name)

    def sync_metadata_from_source(self):
        modified, num_rows = get_engine().get_source_metadata(self)
        self.data_updated = modified
        self.num_rows = num_rows
        self.save()

    @property
    def source_obj(self):
        if self.source == self.Source.INTEGRATION:
            return self.integration
        elif self.source == self.Source.WORKFLOW_NODE:
            return self.workflow_node.workflow
        elif self.source == self.Source.INTERMEDIATE_NODE:
            return self.intermediate_node.workflow
        elif self.source == self.Source.CACHE_NODE:
            return self.cache_node.workflow

    @property
    def out_of_date(self):
        if self.source == self.Source.INTEGRATION:
            if self.integration.kind == self.integration.Kind.SHEET:
                return not self.integration.sheet.up_to_date_with_drive
        elif self.source == self.Source.WORKFLOW_NODE:
            return self.workflow_node.workflow.out_of_date

        return False

    def get_source_url(self):
        return self.source_obj.get_absolute_url()

    @property
    def used_in_workflows(self):
        from apps.workflows.models import Workflow

        return (
            Workflow.objects.filter(nodes__input_table=self.id)
            .distinct()
            .only("name", "project", "created", "updated")
            .annotate(kind=models.Value("Workflow", output_field=models.CharField()))
        )

    @property
    def used_in_dashboards(self):
        from apps.dashboards.models import Dashboard

        return (
            Dashboard.objects.filter(pages__widgets__table=self.id)
            .distinct()
            .only("name", "project", "created", "updated")
            .annotate(kind=models.Value("Dashboard", output_field=models.CharField()))
        )

    @property
    def used_in(self):
        return list(chain(self.used_in_workflows, self.used_in_dashboards))

    def make_clone(self, attrs=None, sub_clone=False, using=None):
        attrs = create_attrs(attrs, self)
        clone = super().make_clone(attrs=attrs, sub_clone=sub_clone, using=using)
        duplicate_table(self, clone)
        return clone
