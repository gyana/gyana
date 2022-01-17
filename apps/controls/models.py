from django.db import models

from apps.base.models import BaseModel


class DateRange(models.TextChoices):
    TODAY = "today", "today"
    TOMORROW = "tomorrow", "tomorrow"
    YESTERDAY = "yesterday", "yesterday"
    ONEWEEKAGO = "oneweekago", "one week ago"
    ONEMONTHAGO = "onemonthago", "one month ago"
    ONEYEARAGO = "oneyearago", "one year ago"
    THIS_WEEK = "thisweek", "This week (starts Monday)"
    THIS_WEEK_UP_TO_DATE = "thisweekuptodate", "This week (starts Monday) up to date"
    LAST_WEEK = "lastweek", "Last week (starts Monday)"
    LAST_7 = "last7", "Last 7 days"
    LAST_14 = "last14", "Last 14 days"
    LAST_28 = "last28", "Last 28 days"
    THIS_MONTH = "thismonth", "This month"
    THIS_MONTH_UP_TO_DATE = "thismonthuptodate", "This month to date"
    LAST_MONTH = "lastmonth", "Last month"
    LAST_30 = "last30", "Last 30 days"
    LAST_90 = "last90", "Last 90 days"
    THIS_QUARTER = "thisquarter", "This quarter"
    THIS_QUARTER_UP_TO_DATE = "thisquarteruptodate", "This quarter up to date"
    LAST_QUARTER = "lastquarter", "Last quarter"
    LAST_180 = "last180", "Last 180 days"
    LAST_12_MONTH = "last12month", "Last 12 months"
    LAST_FULL_12_MONTH = "lastfull12month", "Last full 12 months until today"
    LAST_YEAR = "lastyear", "Last calendar year"
    THIS_YEAR = "thisyear", "This year"
    THIS_YEAR_UP_TO_DATE = "thisyearuptodate", "This year (January - up to date)"


class CustomChoice(models.TextChoices):
    CUSTOM = "custom", "Custom"


class Control(BaseModel):
    class Kind(models.TextChoices):
        DATE_RANGE = "date_range", "Date range"

    kind = models.CharField(max_length=16, default=Kind.DATE_RANGE)
    start = models.DateTimeField(
        blank=True, null=True, help_text="Select the start date"
    )
    end = models.DateTimeField(blank=True, null=True, help_text="Select the end date")
    date_range = models.CharField(
        max_length=20,
        choices=DateRange.choices + CustomChoice.choices,
        blank=True,
        default=DateRange.THIS_YEAR,
        help_text="Select the time period",
    )

    page = models.OneToOneField("dashboards.Page", on_delete=models.CASCADE, null=True)
    widget = models.OneToOneField("widgets.Widget", on_delete=models.CASCADE, null=True)

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
