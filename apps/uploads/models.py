from apps.base.celery import is_bigquery_task_running
from apps.base.models import BaseModel
from apps.integrations.models import Integration
from django.db import models


class Upload(BaseModel):
    class FieldDelimiter(models.TextChoices):
        COMMA = "comma", "Comma"
        TAB = "tab", "Tab"
        PIPE = "pipe", "Pipe"

    integration = models.OneToOneField(Integration, on_delete=models.CASCADE)

    file_gcs_path = models.TextField()
    field_delimiter = models.CharField(
        max_length=8, choices=FieldDelimiter.choices, default=FieldDelimiter.COMMA
    )

    # track the celery task
    sync_task_id = models.UUIDField(null=True)
    sync_started = models.DateTimeField(null=True)

    @property
    def is_syncing(self):
        return is_bigquery_task_running(self.sync_task_id, self.sync_started)

    @property
    def field_delimiter_char(self):
        return FIELD_DELIMITER_CHOICE_TO_CHAR[self.field_delimiter]


FIELD_DELIMITER_CHOICE_TO_CHAR = {
    Upload.FieldDelimiter.COMMA: ",",
    Upload.FieldDelimiter.TAB: "\t",
    Upload.FieldDelimiter.PIPE: "|",
}
