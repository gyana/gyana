from functools import cached_property

from django.conf import settings
from django.db import models
from model_clone.mixins.clone import CloneMixin

from apps.base import clients
from apps.base.models import BaseModel
from apps.projects.models import Project


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
