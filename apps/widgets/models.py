from apps.dashboards.models import Dashboard
from apps.tables.models import Table
from apps.base.aggregations import AggregationFunctions
from apps.base.models import BaseModel
from django.conf import settings
from django.db import models
from model_clone import CloneMixin

DEFAULT_WIDTH = 500
DEFAULT_HEIGHT = 400


class Widget(CloneMixin, BaseModel):
    _clone_m2o_or_o2m_fields = ["filters", "aggregations"]

    class Kind(models.TextChoices):
        TEXT = "text", "Text"
        TABLE = "table", "Table"
        # using fusioncharts name for database
        COLUMN = "mscolumn2d", "Column"
        STACKED_COLUMN = "stackedcolumn2d", "Stacked Column"
        BAR = "msbar2d", "Bar"
        STACKED_BAR = "stackedbar2d", "Stacked Bar"
        LINE = "msline", "Line"
        PIE = "pie2d", "Pie"
        AREA = "area2d", "Area"
        DONUT = "doughnut2d", "Donut"
        SCATTER = "scatter", "Scatter"
        FUNNEL = "funnel", "Funnel"
        PYRAMID = "pyramid", "Pyramid"
        RADAR = "radar", "Radar"
        BUBBLE = "bubble", "Bubble"
        HEATMAP = "heatmap", "Heatmap"

    class Aggregator(models.TextChoices):
        # These aggregators should reflect the names described in the ibis api, none is an exception
        # https://ibis-project.org/docs/api.html#id2
        NONE = "none", "None"
        SUM = "sum", "Sum"
        MEAN = "mean", "Average"

    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE)

    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True)

    # Text attributes
    text_content = models.TextField(null=True, blank=True)

    # Chart attributes
    kind = models.CharField(max_length=32, choices=Kind.choices, default=Kind.COLUMN)
    aggregator = models.CharField(max_length=32, choices=Aggregator.choices)
    # maximum length of bigquery column name
    label = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, null=True, blank=True
    )
    value = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, null=True)

    name = models.CharField(max_length=255, null=True, blank=True)
    sort_by = models.CharField(
        max_length=12, choices=(("label", "Label"), ("value", "Value")), default="label"
    )
    sort_ascending = models.BooleanField(default=True)

    # display state
    width = models.IntegerField(
        default=DEFAULT_WIDTH,
        help_text="The width is in absolute pixel value.",
    )
    height = models.IntegerField(
        default=DEFAULT_HEIGHT,
        help_text="The height is in absolute pixel value.",
    )
    x = models.IntegerField(
        default=0,
        help_text="The x field is in absolute pixel value.",
    )
    y = models.IntegerField(
        default=0,
        help_text="The y field is in absolute pixel value.",
    )

    z = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, null=True, blank=True
    )
    z_aggregator = models.CharField(
        max_length=20, choices=AggregationFunctions.choices, null=True, blank=True
    )

    stack_100_percent = models.BooleanField(default=False)

    def __str__(self):
        return f"<Widget {self.kind} on {self.table}>"

    @property
    def is_valid(self) -> bool:
        """Returns bool stating whether this Widget is ready to be displayed"""
        if self.kind in [self.Kind.TABLE, self.Kind.TEXT]:
            return True
        elif self.kind is not None:
            return self.kind and self.label and self.aggregations.first()

        return False


WIDGET_KIND_TO_WEB = {
    Widget.Kind.TEXT.value: ("fa-text",),
    Widget.Kind.TABLE.value: ("fa-table",),
    Widget.Kind.COLUMN.value: ("fa-chart-bar",),
    Widget.Kind.STACKED_COLUMN.value: ("fa-chart-bar",),
    Widget.Kind.BAR.value: ("fa-chart-bar",),
    Widget.Kind.STACKED_BAR.value: ("fa-chart-bar",),
    Widget.Kind.LINE.value: ("fa-chart-line",),
    Widget.Kind.PIE.value: ("fa-chart-pie",),
    Widget.Kind.AREA.value: ("fa-chart-area",),
    Widget.Kind.DONUT.value: ("fa-dot-circle",),
    Widget.Kind.SCATTER.value: ("fa-chart-scatter",),
    Widget.Kind.FUNNEL.value: ("fa-filter",),
    Widget.Kind.PYRAMID.value: ("fa-triangle",),
    Widget.Kind.RADAR.value: ("fa-radar",),
    Widget.Kind.BUBBLE.value: ("fa-soap",),
    Widget.Kind.HEATMAP.value: ("fa-map",),
}

WIDGET_CHOICES_ARRAY = [
    (choices + WIDGET_KIND_TO_WEB[choices[0]]) for choices in Widget.Kind.choices
]
