from django.db import models
from django.urls import reverse

from apps.base.models import BaseModel


class DateSlicer(BaseModel):
    class Range(models.TextChoices):
        TODAY = "today", "Today"
        YESTERDAY = "yesterday", "Yesterday"
        THIS_WEEK = "thisweek", "This week (starts Monday)"
        LAST_WEEK = "lastweek", "Last week (starts Monday)"
        LAST_7 = "last7", "Last 7 days"
        LAST_14 = "last14", "Last 14 days"
        LAST_28 = "last28", "Last 28 days"
        THIS_MONTH = "thismonth", "This month to date"
        LAST_MONTH = "lastmonth", "Last month"
        LAST_30 = "last30", "Last 30 days"
        LAST_90 = "last90", "Last 90 days"
        THIS_QUARTER = "thisquarter", "This quarter to date"
        LAST_QUARTER = "lastquarter", "Last quarter"
        LAST_180 = "last180", "Last 180 days"
        LAST_12_MONTH = "last12month", "Last 12 months"
        LAST_YEAR = "lastyear", "Last calendar year"
        THIS_YEAR = "thisyear", "This year (January - today)"
        CUSTOM = "custom", "Custom"

    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    date_range = models.CharField(
        max_length=16, choices=Range.choices, blank=True, default=Range.THIS_YEAR
    )

    def __str__(self):
        return self.pk

    def get_absolute_url(self):
        return reverse("dateslicers:detail", args=(self.pk,))
