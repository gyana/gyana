from django.conf import settings
from django.db import models


class Table(models.Model):
    name = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.name
