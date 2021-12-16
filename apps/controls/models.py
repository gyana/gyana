from django.db import models
from django.urls import reverse

from apps.base.models import BaseModel
from apps.filters.models import DateRange


class CustomChoice(models.TextChoices):
    CUSTOM = "custom", "Custom"


class Control(BaseModel):
    class Kind(models.TextChoices):
        DATE_RANGE = "date_range", "Date range"

    kind = models.CharField(max_length=16, default=Kind.DATE_RANGE)
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    date_range = models.CharField(
        max_length=20,
        choices=DateRange.choices + CustomChoice.choices,
        blank=True,
        default=DateRange.THIS_YEAR,
    )

    page = models.OneToOneField("dashboards.Page", on_delete=models.CASCADE)

    def __str__(self):
        return self.pk


class ControlWidget(BaseModel):
    page = models.ForeignKey(
        "dashboards.Page", on_delete=models.CASCADE, related_name="control_widgets"
    )
    control = models.ForeignKey(
        Control, on_delete=models.CASCADE, related_name="widgets"
    )
    x = models.IntegerField(
        default=0,
        help_text="The x field is in absolute pixel value.",
    )
    y = models.IntegerField(
        default=0,
        help_text="The y field is in absolute pixel value.",
    )
