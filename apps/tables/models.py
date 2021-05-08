from apps.projects.models import Project
from django.conf import settings
from django.db import models
from lib.clients import ibis_client


class Table(models.Model):
    class Source(models.TextChoices):
        DATASET = "dataset", "Dataset"
        DATAFLOW_NODE = "dataflow_node", "Dataflow node"
        CONNECTOR = "connector", "Connector"

    bq_table = models.CharField(max_length=settings.BIGQUERY_TABLE_NAME_LENGTH)
    bq_dataset = models.CharField(max_length=settings.BIGQUERY_TABLE_NAME_LENGTH)

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    source = models.CharField(max_length=16, choices=Source.choices)
    # TODO: delete table in bigquery on deletion
    dataset = models.OneToOneField(
        "datasets.Dataset", on_delete=models.CASCADE, null=True
    )
    dataflow_node = models.OneToOneField(
        "dataflows.Node", on_delete=models.CASCADE, null=True
    )
    connector = models.ForeignKey(
        "connectors.Connector", on_delete=models.CASCADE, null=True
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
