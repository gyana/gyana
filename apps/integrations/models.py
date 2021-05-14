import celery
from apps.projects.models import Project
from django.conf import settings
from django.db import models
from django.urls import reverse
from lib.clients import DATASET_ID, ibis_client


class Integration(models.Model):
    class Kind(models.TextChoices):
        GOOGLE_SHEETS = "google_sheets", "Google Sheets"
        CSV = "csv", "CSV"
        FIVETRAN = "fivetran", "Fivetran"

    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    kind = models.CharField(max_length=32, choices=Kind.choices)

    # either a URL or file upload
    url = models.URLField(null=True)
    file = models.FileField(
        upload_to=f"{settings.CLOUD_NAMESPACE}/integrations", null=True
    )

    # bigquery external tables
    external_table_sync_task_id = models.UUIDField(null=True)
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

    def start_sync(self):
        from apps.integrations.tasks import run_external_table_sync

        result = run_external_table_sync.delay(self.id)
        self.external_table_sync_task_id = result.task_id

        self.save()

    @property
    def is_syncing(self):
        if self.external_table_sync_task_id is None:
            return False

        # TODO: Possibly fails for out of date task ids
        # https://stackoverflow.com/a/38267978/15425660
        result = celery.result.AsyncResult(str(self.external_table_sync_task_id))
        return result.status == "PENDING"

    def get_query(self):
        conn = ibis_client()
        if self.kind == Integration.Kind.FIVETRAN:
            return conn.table(self.table_id, database=self.schema)
        return conn.table(self.table_id)

    def get_schema(self):
        return self.get_query().schema()

    def get_table_name(self):
        return f"Integration:{self.name}"

    def get_absolute_url(self):
        return reverse("projects:integrations:detail", args=(self.project.id, self.id))
