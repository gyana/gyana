from django.db import models


class Dataset(models.Model):
    class Kind(models.TextChoices):
        GOOGLE_SHEETS = "google_sheets", "Google Sheets"
        CSV = "csv", "CSV"

    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=32, choices=Kind.choices)

    # either a URL or file upload
    url = models.URLField(null=True)
    file = models.FileField(upload_to="datasets", null=True)

    table_id = models.CharField(max_length=300, null=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.name
