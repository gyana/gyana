from django.db import models
from django.urls import reverse

from apps.base.models import BaseModel
from apps.filters.models import DateRange


class CustomChoice(models.TextChoices):
    CUSTOM = "custom", "Custom"


class DateSlicer(BaseModel):

    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    date_range = models.CharField(
        max_length=20,
        choices=DateRange.choices + CustomChoice.choices,
        blank=True,
        default=DateRange.THIS_YEAR,
    )

    def __str__(self):
        return self.pk

    def get_absolute_url(self):
        return reverse("dateslicers:detail", args=(self.pk,))
