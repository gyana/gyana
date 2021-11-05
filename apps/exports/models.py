from apps.base.models import BaseModel
from apps.nodes.models import Node
from apps.tables.models import Table
from django.conf import settings
from django.db import models
from django.urls import reverse


class Export(BaseModel):
    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        BQ_TABLE_CREATED = "table_created", "Table created"
        EXPORTED = "exported", "Exported"

    node = models.ForeignKey(
        Node, related_name="exports", on_delete=models.CASCADE, null=True
    )
    integration_table = models.ForeignKey(
        Table, related_name="exports", on_delete=models.CASCADE, null=True
    )
    gcs_path = models.CharField(max_length=255)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.RUNNING
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )

    def __str__(self):
        return self.pk

    def get_absolute_url(self):
        return reverse("exports:detail", args=(self.pk,))

    @property
    def table_id(self):
        return f"export_{self.pk}"
