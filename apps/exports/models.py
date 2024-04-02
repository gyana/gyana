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
    file = models.FileField(upload_to="exports/")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )

    exported_at = models.DateTimeField(null=True, editable=False)

    def get_absolute_url(self):
        return reverse("exports:detail", args=(self.pk,))

    @property
    def table_id(self):
        return f"export_{self.pk}"

    @property
    def gcs_uri(self):
        return f"gs://{settings.GS_BUCKET_NAME}/{self.file.name}"
