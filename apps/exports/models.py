import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse

from apps.base.models import BaseModel
from apps.nodes.models import Node
from apps.tables.models import Table


class Export(BaseModel):

    node = models.ForeignKey(
        Node, related_name="exports", on_delete=models.CASCADE, null=True
    )
    integration_table = models.ForeignKey(
        Table, related_name="exports", on_delete=models.CASCADE, null=True
    )
    gcs_id = models.UUIDField(default=uuid.uuid4, editable=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )

    exported_at = models.DateTimeField(null=True, editable=False)

    def __str__(self):
        return self.pk

    def get_absolute_url(self):
        return reverse("exports:detail", args=(self.pk,))

    @property
    def table_id(self):
        return f"export_{self.pk}"

    @property
    def path(self):
        return f"exports/export_{self.pk}_{self.gcs_id}.csv"
