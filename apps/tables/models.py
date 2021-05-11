from apps.projects.models import Project
from django.conf import settings
from django.db import models
from lib.clients import bigquery_client, ibis_client


class Table(models.Model):
    class Source(models.TextChoices):
        INTEGRATION = "integration", "Integration"
        WORKFLOW_NODE = "workflow_node", "Workflow node"

    bq_table = models.CharField(max_length=settings.BIGQUERY_TABLE_NAME_LENGTH)
    bq_dataset = models.CharField(max_length=settings.BIGQUERY_TABLE_NAME_LENGTH)

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    source = models.CharField(max_length=16, choices=Source.choices)
    # TODO: delete table in bigquery on deletion
    integration = models.ForeignKey(
        "integrations.Integration", on_delete=models.CASCADE, null=True
    )
    workflow_node = models.OneToOneField(
        "workflows.Node", on_delete=models.CASCADE, null=True
    )

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return getattr(self, self.source).get_table_name()

    @property
    def bq_id(self):
        return f"{self.bq_dataset}.{self.bq_table}"

    def get_query(self):
        conn = ibis_client()
        return conn.table(self.bq_table, database=self.bq_dataset)

    def get_schema(self):
        return self.get_query().schema()

    def get_bq_schema(self):
        client = bigquery_client()
        bq_table = client.get_table(f"{self.bq_dataset}.{self.bq_table}")
        return bq_table.schema
