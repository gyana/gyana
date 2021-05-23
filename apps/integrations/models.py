import os
import time

import celery
from apps.dashboards.models import Dashboard
from apps.projects.models import Project
from apps.users.models import CustomUser
from apps.workflows.models import Workflow
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from lib.clients import ibis_client


def get_file_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    return f"{settings.CLOUD_NAMESPACE}/integrations/{filename}-{slugify(time.time())}{file_extension}"


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
    file = models.FileField(upload_to=get_file_path, null=True)

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

    created_by = models.ForeignKey(CustomUser, null=True, on_delete=models.SET_NULL)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.name

    @property
    def num_rows(self):
        return self.table_set.all().aggregate(models.Sum("num_rows"))["num_rows__sum"]

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

    @property
    def used_in_workflows(self):
        return Workflow.objects.filter(
            nodes__input_table__in=self.table_set.all()
        ).distinct()

    @property
    def used_in_dashboards(self):
        return Dashboard.objects.filter(
            widget__table__in=self.table_set.all()
        ).distinct()

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

    def icon(self):
        return f"images/integrations/{self.kind}.svg"
