import os
import textwrap
import time
from os.path import splitext

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.base.clients import SLUG
from apps.base.models import BaseModel
from apps.integrations.models import Integration


def upload_to(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    path = f"integrations/{filename}-{slugify(time.time())}{file_extension}"

    if SLUG:
        path = f"{SLUG}/{path}"

    return path


class Upload(BaseModel):
    class FieldDelimiter(models.TextChoices):
        COMMA = "comma", "Comma"
        TAB = "tab", "Tab"
        PIPE = "pipe", "Pipe"

    integration = models.OneToOneField(Integration, on_delete=models.CASCADE, null=True)

    file = models.FileField(upload_to=upload_to)
    field_delimiter = models.CharField(
        max_length=8, choices=FieldDelimiter.choices, default=FieldDelimiter.COMMA
    )

    @property
    def field_delimiter_char(self):
        return FIELD_DELIMITER_CHOICE_TO_CHAR[self.field_delimiter]

    @property
    def table_id(self):
        return f"upload_{self.id:09}"

    @property
    def gcs_uri(self):
        return f"gs://{settings.GS_BUCKET_NAME}/{self.file.name}"

    def create_integration(self, file_name, created_by, project):
        # file_gcs_path has an extra hidden input
        name = textwrap.shorten(splitext(file_name)[0], width=255, placeholder="...")
        integration = Integration.objects.create(
            project=project,
            kind=Integration.Kind.UPLOAD,
            name=name,
            created_by=created_by,
        )
        self.integration = integration


FIELD_DELIMITER_CHOICE_TO_CHAR = {
    Upload.FieldDelimiter.COMMA: ",",
    Upload.FieldDelimiter.TAB: "\t",
    Upload.FieldDelimiter.PIPE: "|",
}
