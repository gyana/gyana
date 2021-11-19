from django.db import models
from django.urls import reverse

from apps.base.models import BaseModel


class DateSlicer(BaseModel):
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.pk

    def get_absolute_url(self):
        return reverse("dateslicers:detail", args=(self.pk,))
