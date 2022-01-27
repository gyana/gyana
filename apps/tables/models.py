from itertools import chain

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from model_clone.mixins.clone import CloneMixin

from apps.base import clients
from apps.base.models import BaseModel
from apps.projects.models import Project
from apps.tables.tasks import copy_table


class AvailableManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(integration__ready=False)


class Table(CloneMixin, BaseModel):
    class Meta:
        unique_together = ["bq_table", "bq_dataset"]
        ordering = ("-created",)

    class Source(models.TextChoices):
        INTEGRATION = "integration", "Integration"
        WORKFLOW_NODE = "workflow_node", "Workflow node"
        INTERMEDIATE_NODE = "intermediate_node", "Intermediate node"
        CACHE_NODE = "cache_node", "Cache node"

    bq_table = models.CharField(max_length=settings.BIGQUERY_TABLE_NAME_LENGTH)
    bq_dataset = models.CharField(max_length=settings.BIGQUERY_TABLE_NAME_LENGTH)

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
        related_name="intermediate_node",
    )
    cache_node = models.OneToOneField(
        "nodes.Node",
        on_delete=models.CASCADE,
        null=True,
        related_name="cache_node",
    )

    num_rows = models.IntegerField(default=0)
    data_updated = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    available = AvailableManager()

    copied_from = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return getattr(self, self.source).get_table_name()

    @property
    def bq_id(self):
        return f"{self.bq_dataset}.{self.bq_table}"

    @property
    def bq_obj(self):
        return clients.bigquery().get_table(self.bq_id)

    @property
    def humanize(self):
        return self.bq_table.replace("_", " ").title()

    @cached_property
    def schema(self):
        from apps.tables.bigquery import get_query_from_table

        return get_query_from_table(self).schema()

    @property
    def owner_name(self):
        if self.source == self.Source.INTEGRATION:
            if self.integration.kind == self.integration.Kind.CONNECTOR:
                return f"{self.integration.name} - {self.bq_table}"
            return self.integration.name
        return f"{self.workflow_node.workflow.name} - {self.workflow_node.name or 'Untitled'}"

    @property
    def bq_dashboard_url(self):
        return f"https://console.cloud.google.com/bigquery?project={settings.GCP_PROJECT}&p={settings.GCP_PROJECT}&d={self.bq_dataset}&t={self.bq_table}&page=table"

    def sync_updates_from_bigquery(self):
        self.data_updated = self.bq_obj.modified
        self.num_rows = self.bq_obj.num_rows
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
        from apps.integrations.models import Integration

        attrs = attrs or {}
        attrs["copied_from"] = self.id
        if self.source == self.Source.INTEGRATION and (
            integration_clone := attrs.get("integration")
        ):
            attrs["project"] = integration_clone.project
            if integration_clone.kindin[
                Integration.Kind.UPLOAD, Integration.Kind.SHEET
            ]:

                attrs["bq_table"] = integration_clone.source_obj.table_id
                attrs["bq_dataset"] = self.bq_dataset
            elif integration_clone.kind == Integration.Kind.CONNECTOR:
                attrs["bq_table"] = self.bq_table
                attrs["bq_dataset"] = self.bq_dataset.replace(
                    self.integration.connector.schema,
                    integration_clone.connector.schema,
                )

            elif integration_clone.kind == Integration.Kind.CUSTOMAPI:
                raise NotImplemented
        elif self.source == self.Source.WORKFLOW_NODE:
            clone_node = attrs["workflow_node"]
            attrs["project"] = clone_node.workflow.project
            attrs["bq_table"] = clone_node.bq_output_table_id
            attrs["bq_dataset"] = self.bq_dataset
        elif self.source == self.Source.INTERMEDIATE_NODE:
            clone_node = attrs["intermediate_node"]
            attrs["project"] = clone_node.workflow.project
            attrs["bq_table"] = clone_node.bq_intermediate_table_id
            attrs["bq_dataset"] = self.bq_dataset
        elif self.source == self.Source.CACHE_NODE:
            clone_node = attrs["cache_node"]
            attrs["project"] = clone_node.workflow.project
            attrs["bq_table"] = clone_node.bq_cache_table_id
            attrs["bq_dataset"] = self.bq_dataset
        clone = super().make_clone(attrs=attrs, sub_clone=sub_clone, using=using)

        copy_table.delay(clone.bq_id, self.bq_id)
        return clone
