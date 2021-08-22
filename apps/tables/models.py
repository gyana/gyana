from functools import cached_property

from django.conf import settings
from django.core.cache import cache
from django.db import models
from google.api_core.exceptions import NotFound

from apps.base.cache import get_cache_key
from apps.base.clients import bigquery_client
from apps.base.models import BaseModel
from apps.projects.models import Project


class AvailableManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(integration__ready=False)


class Table(BaseModel):
    class Meta:
        unique_together = ["bq_table", "bq_dataset"]
        ordering = ("-created",)

    class Source(models.TextChoices):
        INTEGRATION = "integration", "Integration"
        WORKFLOW_NODE = "workflow_node", "Workflow node"
        PIVOT_NODE = "intermediate_node", "Intermediate node"

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

    num_rows = models.IntegerField(default=0)
    data_updated = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    available = AvailableManager()

    def __str__(self):
        return getattr(self, self.source).get_table_name()

    def save(self, *args, **kwargs):
        # Tables can exist before their respective bq_table entity exists. Defaults to num_rows 0
        try:
            self.num_rows = self.bq_obj.num_rows
        except (NameError, NotFound):
            self.num_rows = 0

        super().save(*args, **kwargs)

    @property
    def bq_external_table_id(self):
        return f"table_{self.id}_external"

    @property
    def bq_id(self):
        return f"{self.bq_dataset}.{self.bq_table}"

    @property
    def bq_obj(self):
        return bigquery_client().get_table(self.bq_id)

    @property
    def cache_key(self):
        return get_cache_key(id=self.id, data_updated=str(self.data_updated))

    @property
    def humanize(self):
        return self.bq_table.replace("_", " ").title()

    @cached_property
    def schema(self):

        from apps.tables.bigquery import get_query_from_table

        if (res := cache.get(self.cache_key)) is None:
            res = get_query_from_table(self).schema()
            cache.set(self.cache_key, res, 30)

        return res

    @property
    def owner_name(self):
        if self.source == self.Source.INTEGRATION:
            if self.integration.kind == self.integration.Kind.CONNECTOR:
                return f"{self.integration.name} - {self.bq_table}"
            return self.integration.name
        return f"{self.workflow_node.workflow.name} - {self.workflow_node.output_name or 'Untitled'}"
