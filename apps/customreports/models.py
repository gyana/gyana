from django.conf import settings
from django.db import models

from apps.base.fields import ChoiceArrayField
from apps.base.models import BaseModel
from apps.connectors.fivetran.services import facebook_ads


def default_fields():
    return ["ad_id"]


class FacebookAdsCustomReport(BaseModel):
    FIELD_CHOICES = zip(facebook_ads.FIELDS, facebook_ads.FIELDS)
    BREAKDOWN_CHOICES = zip(facebook_ads.BREAKDOWNS, facebook_ads.BREAKDOWNS)
    ACTION_BREAKDOWN_CHOICES = zip(
        facebook_ads.ACTION_BREAKDOWNS, facebook_ads.ACTION_BREAKDOWNS
    )

    class Aggregation(models.TextChoices):
        Day = "Day", "Day"
        Week = "Week", "Week"
        Month = "Month", "Month"
        Lifetime = "Lifetime", "Lifetime"

    class ActionReportTime(models.TextChoices):
        impression = "impression", "Impression"
        conversion = "conversion", "Conversion"

    class AttributionWindow(models.TextChoices):
        NONE = "NONE", "None"
        DAY_1 = "DAY_1", "Day 1"
        DAY_7 = "DAY_7", "Day 7"

    table_name = models.CharField(
        max_length=settings.BIGQUERY_TABLE_NAME_LENGTH, default="Untitled custom report"
    )
    fields = ChoiceArrayField(
        models.CharField(max_length=64, choices=FIELD_CHOICES),
        default=default_fields,
    )
    breakdowns = ChoiceArrayField(
        models.CharField(max_length=64, choices=BREAKDOWN_CHOICES),
        default=list,
        blank=True,
    )
    action_breakdowns = ChoiceArrayField(
        models.CharField(max_length=64, choices=ACTION_BREAKDOWN_CHOICES),
        default=list,
        blank=True,
    )
    aggregation = models.CharField(
        max_length=8, choices=Aggregation.choices, default=Aggregation.Day
    )
    action_report_time = models.CharField(
        max_length=16,
        choices=ActionReportTime.choices,
        default=ActionReportTime.impression,
    )
    click_attribution_window = models.CharField(
        max_length=16,
        choices=AttributionWindow.choices,
        default=AttributionWindow.DAY_7,
    )
    view_attribution_window = models.CharField(
        max_length=16,
        choices=AttributionWindow.choices,
        default=AttributionWindow.DAY_1,
    )
    use_unified_attribution_setting = models.BooleanField(default=True)
    connector = models.ForeignKey("connectors.Connector", on_delete=models.CASCADE)
