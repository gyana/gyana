from apps.dashboards.models import Dashboard
from apps.tables.models import Table
from django.db import models
from django.db.models.aggregates import Max


class Widget(models.Model):
    class Kind(models.TextChoices):
        TABLE = "table", "Table"
        # using fusioncharts name for database
        COLUMN = "column2d", "Column"
        LINE = "line", "Line"
        PIE = "pie2d", "Pie"

    class Aggregator(models.TextChoices):
        # These aggregators should reflect the names described in the ibis api, none is an exception
        # https://ibis-project.org/docs/api.html#id2
        NONE = "none", "None"
        SUM = "sum", "Sum"
        MEAN = "mean", "Average"

    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE)

    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True)

    # Chart attributes
    kind = models.CharField(max_length=32, choices=Kind.choices)
    aggregator = models.CharField(max_length=32, choices=Aggregator.choices)
    # maximum length of bigquery column name
    label = models.CharField(max_length=300, null=True, blank=True)
    value = models.CharField(max_length=300, null=True, blank=True)

    description = models.CharField(max_length=255, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return f"<Widget {self.kind} on {self.table}>"

    @property
    def is_valid(self) -> bool:
        """Returns bool stating whether this Widget is ready to be displayed"""
        if self.kind == self.Kind.TABLE:
            return True
        elif self.kind is not None:
            return self.kind and self.label and self.value and self.aggregator

        return False
