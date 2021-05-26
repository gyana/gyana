from functools import cached_property

from apps.projects.models import Project
from apps.tables.models import Table
from apps.workflows.nodes import NODE_FROM_CONFIG
from django.conf import settings
from django.db import models
from django.db.models.fields import related
from django.urls import reverse


class Workflow(models.Model):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    last_run = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("projects:workflows:detail", args=(self.project.id, self.id))

    @property
    def failed(self):
        return any(node.error is not None for node in self.nodes.all())


NodeConfig = {
    "input": {
        "displayName": "Input",
        "icon": "fa-layer-group",
        "description": "Select a table from an Integration or previous Workflow",
        "section": "Input/Output",
    },
    "output": {
        "displayName": "Output",
        "icon": "fa-table",
        "description": "Save result as a new table",
        "section": "Input/Output",
    },
    "select": {
        "displayName": "Select",
        "icon": "fa-lasso",
        "description": "Select columns from the table",
        "section": "Table manipulations",
    },
    "join": {
        "displayName": "Join",
        "icon": "fa-link",
        "description": "Combine rows from two tables based on a common column",
        "maxParents": 2,
        "section": "Table manipulations",
    },
    "aggregation": {
        "displayName": "Aggregation",
        "icon": "fa-object-group",
        "description": "Aggregate values by grouping columns",
        "section": "Table manipulations",
    },
    "union": {
        "displayName": "Union",
        "icon": "fa-union",
        "description": "Combine two or more tables on top of each other",
        "maxParents": -1,
        "section": "Table manipulations",
    },
    "sort": {
        "displayName": "Sort",
        "icon": "fa-sort-numeric-up",
        "description": "Sort rows by the values of the specified columns",
        "section": "Table manipulations",
    },
    "limit": {
        "displayName": "Limit",
        "icon": "fa-sliders-h-square",
        "description": "Keep a set number of of rows",
        "section": "Table manipulations",
    },
    "filter": {
        "displayName": "Filter",
        "icon": "fa-filter",
        "description": "Filter rows by specified criteria",
        "section": "Table manipulations",
    },
    "edit": {
        "displayName": "Edit",
        "icon": "fa-edit",
        "description": "Change a columns value",
        "section": "Column manipulations",
    },
    "add": {
        "displayName": "Add",
        "icon": "fa-plus",
        "description": "Add new columns to the table",
        "section": "Column manipulations",
    },
}


class Node(models.Model):
    class Kind(models.TextChoices):
        INPUT = "input", "Input"
        OUTPUT = "output", "Output"
        SELECT = "select", "Select"
        JOIN = "join", "Join"
        AGGREGATION = "aggregation", "Aggregation"
        UNION = "union", "Union"
        SORT = "sort", "Sort"
        LIMIT = "limit", "Limit"
        FILTER = "filter", "Filter"
        EDIT = "edit", "Edit"
        ADD = "add", "Add"

    workflow = models.ForeignKey(
        Workflow, on_delete=models.CASCADE, related_name="nodes"
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    x = models.FloatField()
    y = models.FloatField()
    parents = models.ManyToManyField(
        "self", symmetrical=False, related_name="children", blank=True
    )
    error = models.CharField(max_length=300, null=True)

    # ======== Node specific columns ========= #

    # Input
    input_table = models.ForeignKey(Table, on_delete=models.CASCADE, null=True)

    # Output
    output_name = models.CharField(max_length=100, null=True)

    # Select
    # columns exists on Column as FK

    # Aggregation
    # columns exists on Column as FK
    # aggregations exists on FunctionColumn as FK

    # Join
    join_how = models.CharField(
        max_length=12,
        choices=[
            ("inner", "Inner"),
            ("outer", "Outer"),
            ("left", "Left"),
            ("right", "Right"),
        ],
        default="inner",
    )
    join_left = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, null=True, blank=True
    )
    join_right = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, null=True, blank=True
    )

    # Union

    union_distinct = models.BooleanField(default=False)

    # Sort
    # handled via ForeignKey on SortModel

    # Filter
    # handled by the Filter model in *apps/filters/models.py*

    # Edit and Add
    # handled via ForeignKey on EditModel

    # Limit

    limit_limit = models.IntegerField(default=100)
    limit_offset = models.IntegerField(null=True)

    def get_query(self):
        func = NODE_FROM_CONFIG[self.kind]
        try:
            query = func(self)
            if self.error:
                self.error = None
                self.save()
            return query
        except Exception as err:
            self.error = str(err)
            self.save()

    @cached_property
    def schema(self):
        return self.get_query().schema()

    def get_table_name(self):
        return f"Workflow:{self.workflow.name}:{self.output_name}"


class Column(models.Model):
    name = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="columns")


class FunctionColumn(models.Model):
    class Functions(models.TextChoices):
        # These functions need to correspond to ibis Column methods
        # https://ibis-project.org/docs/api.html
        SUM = "sum", "Sum"
        COUNT = "count", "Count"
        MEAN = "mean", "Average"
        MAX = "max", "Maximum"
        MIN = "min", "Minimum"
        STD = "std", "Standard deviation"

    name = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
    function = models.CharField(max_length=20, choices=Functions.choices)
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="aggregations"
    )


class SortColumn(models.Model):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="sort_columns"
    )
    ascending = models.BooleanField(default=True)
    name = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)


class Operations(models.TextChoices):
    LOWER = "lower", "to lowercase"
    UPPER = "upper", "to uppercase"
    ISNULL = "isnull", "is null"
    CUMMAX = "cummax", "cummulative max"
    CUMMIN = "cummin", "cummulative min"
    ABS = "abs", "absolute value"
    SQRT = "sqrt", "square root"


class EditColumn(models.Model):

    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="edit_columns"
    )
    name = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
    function = models.CharField(max_length=20, choices=Operations.choices)


class AddColumn(models.Model):

    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="add_columns")
    name = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
    function = models.CharField(max_length=20, choices=Operations.choices)
    label = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
