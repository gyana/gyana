from apps.dashboards.models import Dashboard
from apps.tables.models import Table
from django.db import models


class Widget(models.Model):
    class Kind(models.TextChoices):
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

    name = models.CharField(max_length=255)
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE)

    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True)

    kind = models.CharField(max_length=32, choices=Kind.choices)
    aggregator = models.CharField(max_length=32, choices=Aggregator.choices)
    # maximum length of bigquery column name
    label = models.CharField(max_length=300, null=True, blank=True)
    value = models.CharField(max_length=300, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.name

    def is_valid(self) -> bool:
        """Returns bool stating whether this Widget is ready to be displayed"""
        return self.kind and self.label and self.value and self.aggregator
