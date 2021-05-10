from apps.projects.models import Project
from django.db import models
from lib.clients import ibis_client


class Dataset(models.Model):
    class Kind(models.TextChoices):
        GOOGLE_SHEETS = "google_sheets", "Google Sheets"
        CSV = "csv", "CSV"
        FIVETRAN = "fivetran", "Fivetran"

    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    kind = models.CharField(max_length=32, choices=Kind.choices)

    # either a URL or file upload
    url = models.URLField(null=True)
    file = models.FileField(upload_to="datasets", null=True)

    # bigquery external tables
    has_initial_sync = models.BooleanField(default=False)
    last_synced = models.DateTimeField(null=True)

    # fivetran
    service = models.TextField(max_length=255, null=True)
    fivetran_id = models.TextField(null=True)
    schema = models.TextField(null=True)
    fivetran_authorized = models.BooleanField(default=False)
    fivetran_poll_historical_sync_task_id = models.UUIDField(null=True)
    historical_sync_complete = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.name

    def get_query(self):
        conn = ibis_client()
        return conn.table(self.table_id)

    def get_schema(self):
        return self.get_query().schema()

    def get_table_name(self):
        return f"Dataset:{self.name}"
