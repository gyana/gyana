from apps.projects.models import Project
from django.conf import settings
from django.db import models


class Table(models.Model):
    bq_table = models.CharField(max_length=settings.BIGQUERY_TABLE_NAME_LENGTH)
    bq_dataset = models.CharField(max_length=settings.BIGQUERY_TABLE_NAME_LENGTH)

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

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
        return self.name
