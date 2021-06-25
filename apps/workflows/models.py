import logging
from functools import cached_property

from apps.projects.models import Project
from apps.tables.models import Table
from apps.workflows.nodes import (
    NODE_FROM_CONFIG,
    CommonOperations,
    DateOperations,
    DatetimeOperations,
    NumericOperations,
    StringOperations,
    TimeOperations,
)
from dirtyfields import DirtyFieldsMixin
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Workflow(models.Model):
    name = models.CharField(max_length=255, default="Untitled")
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    last_run = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project_workflows:detail", args=(self.project.id, self.id))

    @property
    def failed(self):
        return any(node.error is not None for node in self.nodes.all())

    @property
    def out_of_date(self):
        return self.last_run < self.updated if self.last_run else True


NodeConfig = {
    "input": {
        "displayName": "Get data",
        "icon": "fa-layer-group",
        "description": "Select a table from an Integration or previous Workflow",
        "section": "Input/Output",
    },
    "output": {
        "displayName": "Save data",
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
    "rename": {
        "displayName": "Rename",
        "icon": "fa-keyboard",
        "description": "Rename columns",
        "section": "Column manipulations",
    },
    "text": {
        "displayName": "Text",
        "icon": "fa-text",
        "description": "Annotate your workflow",
        "section": "Annotation",
        "maxParents": 0,
    },
    "formula": {
        "displayName": "Formula",
        "icon": "fa-function",
        "description": "Add a new column using a formula",
        "section": "Column manipulations",
    },
    "distinct": {
        "displayName": "Distinct",
        "icon": "fa-fingerprint",
        "description": "Select unqiue values from selected columns",
        "section": "Table manipulations",
    },
    "pivot": {
        "displayName": "Pivot",
        "icon": "fa-redo-alt",
        "description": "Pivot your table",
        "section": "Table manipulations",
    },
    "unpivot": {
        "displayName": "Unpivot",
        "icon": "fa-redo-alt",
        "description": "Unpivot your table",
        "section": "Table manipulations",
    },
}


class AggregationFunctions(models.TextChoices):
    # These functions need to correspond to ibis Column methods
    # https://ibis-project.org/docs/api.html
    SUM = "sum", "Sum"
    COUNT = "count", "Count"
    MEAN = "mean", "Average"
    MAX = "max", "Maximum"
    MIN = "min", "Minimum"
    STD = "std", "Standard deviation"


class Node(DirtyFieldsMixin, models.Model):
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
        RENAME = "rename", "Rename"
        TEXT = "text", "Text"
        FORMULA = "formula", "Formula"
        DISTINCT = "distinct", "Distinct"
        PIVOT = "pivot", "Pivot"
        UNPIVOT = "unpivot", "Unpivot"

    workflow = models.ForeignKey(
        Workflow, on_delete=models.CASCADE, related_name="nodes"
    )
    name = models.CharField(max_length=64, null=True, blank=True)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    x = models.FloatField()
    y = models.FloatField()
    parents = models.ManyToManyField(
        "self", symmetrical=False, related_name="children", blank=True
    )

    created = models.DateTimeField(auto_now_add=True, editable=False)
    data_updated = models.DateTimeField(auto_now_add=True, editable=False)

    error = models.CharField(max_length=300, null=True)
    intermediate_table = models.ForeignKey(
        Table, on_delete=models.CASCADE, null=True, related_name="intermediate_table"
    )
    # ======== Node specific columns ========= #

    # Input
    input_table = models.ForeignKey(Table, on_delete=models.CASCADE, null=True)

    # Output
    output_name = models.CharField(max_length=100, null=True)

    # Select, Distinct
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

    # Filter
    # handled by the Filter model in *apps/filters/models.py*

    # Sort, Edit, Add, and Rename
    # handled via ForeignKey on SortColumn EditColumn, AddColumn, and RenameColumn respectively

    # Limit

    limit_limit = models.IntegerField(default=100)
    limit_offset = models.IntegerField(null=True)

    # Text
    text_text = models.TextField(null=True)

    # Pivot
    pivot_index = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, null=True, blank=True
    )
    pivot_column = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, null=True, blank=True
    )
    pivot_value = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, null=True, blank=True
    )
    pivot_aggregation = models.CharField(
        max_length=20, choices=AggregationFunctions.choices, null=True, blank=True
    )

    unpivot_value = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, null=True, blank=True
    )
    unpivot_column = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        super(Node, self).save(*args, **kwargs)
        self.workflow.save()

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
            logging.error(err, exc_info=err)

    @cached_property
    def schema(self):
        return self.get_query().schema()

    def get_table_name(self):
        return f"Workflow:{self.workflow.name}:{self.output_name}"

    def save(self, *args, **kwargs) -> None:
        dirty_fields = set(self.get_dirty_fields(check_relationship=True).keys()) - {
            "name",
            "x",
            "y",
            "error",
        }

        if dirty_fields and "data_updated" not in dirty_fields:
            self.data_updated = timezone.now()

        return super().save(*args, **kwargs)


class SaveParentModel(DirtyFieldsMixin, models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs) -> None:
        if self.is_dirty():
            self.node.data_updated = timezone.now()
            self.node.save()
        return super().save(*args, **kwargs)


class Column(SaveParentModel):
    column = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="columns")


class SecondaryColumn(SaveParentModel):
    column = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="secondary_columns"
    )


class FunctionColumn(SaveParentModel):

    column = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
    function = models.CharField(max_length=20, choices=AggregationFunctions.choices)
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="aggregations"
    )


class SortColumn(SaveParentModel):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="sort_columns"
    )
    ascending = models.BooleanField(default=True)
    column = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)


class AbstractOperationColumn(SaveParentModel):
    class Meta:
        abstract = True

    column = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)

    string_function = models.CharField(
        max_length=20,
        choices=(
            (key, value.label)
            for key, value in {**CommonOperations, **StringOperations}.items()
        ),
        null=True,
    )
    integer_function = models.CharField(
        max_length=20,
        choices=(
            (key, value.label)
            for key, value in {**CommonOperations, **NumericOperations}.items()
        ),
        null=True,
    )
    date_function = models.CharField(
        max_length=20,
        choices=(
            (key, value.label)
            for key, value in {**CommonOperations, **DateOperations}.items()
        ),
        null=True,
    )
    time_function = models.CharField(
        max_length=20,
        choices=(
            (key, value.label)
            for key, value in {**CommonOperations, **TimeOperations}.items()
        ),
        null=True,
    )
    datetime_function = models.CharField(
        max_length=20,
        choices=(
            (key, value.label)
            for key, value in {
                **CommonOperations,
                **TimeOperations,
                **DateOperations,
                **DatetimeOperations,
            }.items()
        ),
        null=True,
    )

    integer_value = models.BigIntegerField(null=True, blank=True)
    float_value = models.FloatField(null=True, blank=True)
    string_value = models.TextField(null=True, blank=True)

    @property
    def function(self):
        return (
            self.string_function
            or self.integer_function
            or self.date_function
            or self.time_function
            or self.datetime_function
        )


class EditColumn(AbstractOperationColumn):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="edit_columns"
    )


bigquery_column_regex = RegexValidator(
    r"^[a-zA-Z_][0-9a-zA-Z_]*$", "Only numbers, letters and underscores allowed."
)


class AddColumn(AbstractOperationColumn):
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="add_columns")
    label = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        validators=[bigquery_column_regex],
    )


class RenameColumn(SaveParentModel):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="rename_columns"
    )
    column = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
    new_name = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        validators=[bigquery_column_regex],
    )


class FormulaColumn(SaveParentModel):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="formula_columns"
    )
    formula = models.TextField(null=True, blank=True)
    label = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        validators=[bigquery_column_regex],
    )
