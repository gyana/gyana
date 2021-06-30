from apps.dashboards.models import Dashboard
from apps.tables.models import Table
from django.db import models
from model_clone import CloneMixin

DEFAULT_WIDTH = 50
DEFAULT_HEIGHT = 400


class Widget(CloneMixin, models.Model):
    _clone_m2o_or_o2m_fields = ["filters"]

    class Kind(models.TextChoices):
        TEXT = "text", "Text"
        TABLE = "table", "Table"
        # using fusioncharts name for database
        COLUMN = "column2d", "Column"
        LINE = "line", "Line"
        PIE = "pie2d", "Pie"
        AREA = "area2d", "Area"
        DONUT = "doughnut2d", "Donut"
        SCATTER = "scatter", "Scatter"
        FUNNEL = "funnel", "Funnel"
        PYRAMID = "pyramid", "Pyramid"
        RADAR = "radar", "Radar"

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
    label = models.CharField(max_length=300, null=True, blank=True)
    value = models.CharField(max_length=300, null=True, blank=True)

    description = models.CharField(max_length=255, null=True, blank=True)

    # display state
    width = models.IntegerField(
        default=DEFAULT_WIDTH,
        help_text="The width is relative. Relative widths avoid overflow on different displays",
    )
    height = models.IntegerField(
        default=DEFAULT_HEIGHT,
        help_text="The height is absolute. We allow for scrollable dashboards in the y-axis.",
    )
    x = models.IntegerField(
        default=0,
        help_text="The x field is relative, this avoids overflow on the x-axis in a dashboard.",
    )
    y = models.IntegerField(
        default=0,
        help_text="The y field is absolute, we allow for overflow on the y-axis in a dashboard.",
    )

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return f"<Widget {self.kind} on {self.table}>"

    @property
    def is_valid(self) -> bool:
        """Returns bool stating whether this Widget is ready to be displayed"""
        if self.kind == self.Kind.TABLE or self.kind == self.Kind.TEXT:
            return True
        elif self.kind is not None:
            return self.kind and self.label and self.value and self.aggregator

        return False


WIDGET_KIND_TO_WEB = {
    Widget.Kind.TEXT.value: ("fa-text",),
    Widget.Kind.TABLE.value: ("fa-table",),
    Widget.Kind.COLUMN.value: ("fa-chart-bar",),
    Widget.Kind.LINE.value: ("fa-chart-line",),
    Widget.Kind.PIE.value: ("fa-chart-pie",),
    Widget.Kind.AREA.value: ("fa-chart-area",),
    Widget.Kind.DONUT.value: ("fa-dot-circle",),
    Widget.Kind.SCATTER.value: ("fa-chart-scatter",),
    Widget.Kind.FUNNEL.value: ("fa-filter",),
    Widget.Kind.PYRAMID.value: ("fa-triangle",),
    Widget.Kind.RADAR.value: ("fa-radar",),
}

WIDGET_CHOICES_ARRAY = [
    (choices + WIDGET_KIND_TO_WEB[choices[0]]) for choices in Widget.Kind.choices
]
