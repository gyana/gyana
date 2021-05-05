from apps.projects.models import Project
from django.db import models


class Dataset(models.Model):
    class Kind(models.TextChoices):
        GOOGLE_SHEETS = "google_sheets", "Google Sheets"
        CSV = "csv", "CSV"

    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    kind = models.CharField(max_length=32, choices=Kind.choices)

    # either a URL or file upload
    url = models.URLField(null=True)
    file = models.FileField(upload_to="datasets", null=True)

    has_initial_sync = models.BooleanField(default=False)
    last_synced = models.DateTimeField(null=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.name

    @property
    def table_id(self):
        return f"table_{self.pk}"

    @property
    def external_table_id(self):
        return f"table_{self.pk}_external"
