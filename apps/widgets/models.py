from django.conf import settings
from django.db import models
from model_clone import CloneMixin

from apps.base.aggregations import AggregationFunctions
from apps.base.models import BaseModel
from apps.dashboards.models import Dashboard
from apps.tables.models import Table

# Need to be a multiple of GRID_SIZE found in GyWidget.tsx
DEFAULT_WIDTH = 495
DEFAULT_HEIGHT = 390


class Widget(CloneMixin, BaseModel):
    _clone_m2o_or_o2m_fields = ["filters", "aggregations"]

    class Category(models.TextChoices):
        SIMPLE = "simple", "Simple"
        TIMESERIES = "timeseries", "Timeseries"
        ADVANCED = "advanced", "Advanced"

    class Kind(models.TextChoices):
        TEXT = "text", "Text"
        METRIC = "metric", "Metric"
        TABLE = "table", "Table"
        # using fusioncharts name for database
        COLUMN = "mscolumn2d", "Column"
        STACKED_COLUMN = "stackedcolumn2d", "Stacked Column"
        BAR = "msbar2d", "Bar"
        STACKED_BAR = "stackedbar2d", "Stacked Bar"
        LINE = "msline", "Line"
        STACKED_LINE = "msline-stacked", "Stacked Line"
        PIE = "pie2d", "Pie"
        AREA = "msarea", "Area"
        DONUT = "doughnut2d", "Donut"
        SCATTER = "scatter", "Scatter"
        FUNNEL = "funnel", "Funnel"
        PYRAMID = "pyramid", "Pyramid"
        RADAR = "radar", "Radar"
        BUBBLE = "bubble", "Bubble"
        HEATMAP = "heatmap", "Heatmap"
        TIMESERIES_LINE = "timeseries-line", "Line"
        TIMESERIES_STACKED_LINE = "timeseries-line_stacked", "Stacked Line"
        TIMESERIES_COLUMN = "timeseries-column", "Column"
        TIMESERIES_STACKED_COLUMN = (
            "timeseries-column-stacked",
            "Stacked Column",
        )
        TIMESERIES_AREA = "timeseries-area", "Area"

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
    dimension = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        null=True,
    )
    second_dimension = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, null=True
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    sort_by = models.CharField(
        max_length=12,
        choices=(("dimension", "Dimension"), ("metric", "Metric")),
        default="dimension",
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

    stack_100_percent = models.BooleanField(default=False)
    error = models.CharField(max_length=300, null=True)

    _clone_m2o_or_o2m_fields = [
        "aggregations",
        "filters",
    ]

    def __str__(self):
        return f"<Widget {self.kind} on {self.table}>"

    @property
    def is_valid(self) -> bool:
        """Returns bool stating whether this Widget is ready to be displayed"""
        # TODO: right now you also need to update the query in DashboardOverview dashboards/frames
        if self.kind == self.Kind.TEXT:
            return True
        if not self.table:
            return False
        if self.kind == self.Kind.TABLE:
            return True
        if self.kind == self.Kind.METRIC:
            return self.aggregations.count() == 1
        if self.kind == self.Kind.RADAR:
            return self.aggregations.count() >= 3
        if self.kind in [self.Kind.FUNNEL, self.Kind.PYRAMID]:
            return self.aggregations.count() >= 2
        if self.kind is not None:
            return bool(self.kind and self.dimension)

        return False

    @property
    def category(self):
        return WIDGET_KIND_TO_WEB[self.kind][1]


NO_DIMENSION_WIDGETS = [
    Widget.Kind.RADAR,
    Widget.Kind.FUNNEL,
    Widget.Kind.PYRAMID,
    Widget.Kind.METRIC,
]

WIDGET_KIND_TO_WEB = {
    Widget.Kind.TEXT.value: ("fa-text", Widget.Category.SIMPLE),
    Widget.Kind.METRIC.value: ("fa-value-absolute", Widget.Category.SIMPLE),
    Widget.Kind.TABLE.value: ("fa-table", Widget.Category.SIMPLE),
    Widget.Kind.COLUMN.value: ("fa-chart-bar", Widget.Category.SIMPLE),
    Widget.Kind.STACKED_COLUMN.value: ("fa-chart-bar", Widget.Category.ADVANCED),
    Widget.Kind.BAR.value: ("fa-chart-bar", Widget.Category.SIMPLE),
    Widget.Kind.STACKED_BAR.value: ("fa-chart-bar", Widget.Category.ADVANCED),
    Widget.Kind.LINE.value: ("fa-chart-line", Widget.Category.SIMPLE),
    Widget.Kind.STACKED_LINE.value: ("fa-chart-line", Widget.Category.ADVANCED),
    Widget.Kind.PIE.value: ("fa-chart-pie", Widget.Category.SIMPLE),
    Widget.Kind.AREA.value: ("fa-chart-area", Widget.Category.ADVANCED),
    Widget.Kind.DONUT.value: ("fa-dot-circle", Widget.Category.SIMPLE),
    Widget.Kind.SCATTER.value: ("fa-chart-scatter", Widget.Category.ADVANCED),
    Widget.Kind.FUNNEL.value: ("fa-filter", Widget.Category.ADVANCED),
    Widget.Kind.PYRAMID.value: ("fa-triangle", Widget.Category.ADVANCED),
    Widget.Kind.RADAR.value: ("fa-radar", Widget.Category.ADVANCED),
    Widget.Kind.BUBBLE.value: ("fa-soap", Widget.Category.ADVANCED),
    Widget.Kind.HEATMAP.value: ("fa-map", Widget.Category.ADVANCED),
    Widget.Kind.TIMESERIES_LINE.value: ("fa-chart-line", Widget.Category.TIMESERIES),
    Widget.Kind.TIMESERIES_STACKED_LINE.value: (
        "fa-chart-line",
        Widget.Category.TIMESERIES,
    ),
    Widget.Kind.TIMESERIES_COLUMN.value: ("fa-chart-bar", Widget.Category.TIMESERIES),
    Widget.Kind.TIMESERIES_STACKED_COLUMN.value: (
        "fa-chart-bar",
        Widget.Category.TIMESERIES,
    ),
    Widget.Kind.TIMESERIES_AREA.value: ("fa-chart-area", Widget.Category.TIMESERIES),
}


WIDGET_CHOICES_ARRAY = [
    (choices + WIDGET_KIND_TO_WEB[choices[0]]) for choices in Widget.Kind.choices
]


COUNT_COLUMN_NAME = "count"
