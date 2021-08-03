from functools import cached_property

from apps.nodes.config import NODE_CONFIG
from apps.tables.models import Table
from apps.utils.aggregations import AggregationFunctions
from apps.utils.cache import get_cache_key
from apps.utils.models import BaseModel
from apps.workflows.models import Workflow
from dirtyfields import DirtyFieldsMixin
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import Max
from django.utils import timezone
from model_clone import CloneMixin


class Node(DirtyFieldsMixin, CloneMixin, BaseModel):
    class Kind(models.TextChoices):
        INPUT = "input", "Get data"
        OUTPUT = "output", "Save data"
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
        INTERSECT = "intersect", "Intersection"
        WINDOW = "window", "Window"

    # You have to add new many-to-one relations here
    _clone_m2o_or_o2m_fields = [
        "filters",
        "columns",
        "secondary_columns",
        "aggregations",
        "sort_columns",
        "edit_columns",
        "add_columns",
        "rename_columns",
        "formula_columns",
        "window_columns",
    ]

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

    data_updated = models.DateTimeField(null=True, editable=False)

    error = models.CharField(max_length=300, null=True)
    intermediate_table = models.ForeignKey(
        Table, on_delete=models.CASCADE, null=True, related_name="intermediate_table"
    )
    # ======== Node specific columns ========= #

    # Input
    input_table = models.ForeignKey(
        Table, on_delete=models.CASCADE, null=True, help_text="Select a data source"
    )

    # Output
    output_name = models.CharField(
        max_length=100,
        null=True,
        help_text="Name your output, this name will be refered to in other workflows or dashboards.",
    )

    # Select also uses columns
    select_mode = models.CharField(
        max_length=8,
        choices=(("keep", "keep"), ("exclude", "exclude")),
        default="keep",
        help_text="Either keep or exclude the selected columns",
    )
    # Distinct
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
        help_text="Select the join method, more information in the docs",
    )
    join_left = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        null=True,
        blank=True,
        help_text="The column from the first parent you want to join on.",
    )
    join_right = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        null=True,
        blank=True,
        help_text="The column from the second parent you want to join on.",
    )

    # Union

    union_mode = models.CharField(
        max_length=8,
        choices=(("keep", "keep"), ("exclude", "exclude")),
        default="except",
        help_text="Either keep or exclude the common rows",
    )
    union_distinct = models.BooleanField(
        default=False, help_text="Ignore common rows if selected"
    )

    # Filter
    # handled by the Filter model in *apps/filters/models.py*

    # Sort, Edit, Add, and Rename
    # handled via ForeignKey on SortColumn EditColumn, AddColumn, and RenameColumn respectively

    # Limit

    limit_limit = models.IntegerField(
        default=100, help_text="Limits rows to selected number"
    )
    limit_offset = models.IntegerField(
        null=True, help_text="From where to start the limit"
    )

    # Text
    text_text = models.TextField(null=True)

    # Pivot
    pivot_index = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        null=True,
        blank=True,
        help_text="Which column to keep as index",
    )
    pivot_column = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        null=True,
        blank=True,
        help_text="The column whose values create the new column names",
    )
    pivot_value = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        null=True,
        blank=True,
        help_text="The column containing the values for the new pivot cells",
    )
    pivot_aggregation = models.CharField(
        max_length=20,
        choices=AggregationFunctions.choices,
        null=True,
        blank=True,
        help_text="Select an aggregation to be applied to the new cells",
    )

    unpivot_value = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        null=True,
        blank=True,
        help_text="Name of the new value column",
    )
    unpivot_column = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        null=True,
        blank=True,
        help_text="Name of the new category column",
    )

    def save(self, *args, **kwargs):
        dirty_fields = set(self.get_dirty_fields(check_relationship=True).keys()) - {
            "name",
            "x",
            "y",
            "error",
        }
        if dirty_fields:
            self.workflow.data_updated = timezone.now()
            self.workflow.save()
        if dirty_fields and "data_updated" not in dirty_fields:
            self.data_updated = timezone.now()

        return super().save(*args, **kwargs)

    @cached_property
    def schema(self):

        from .bigquery import get_query_from_node

        # in theory, we only need to fetch all parent nodes recursively
        # in practice, this is faster and less error prone
        nodes_last_updated = self.workflow.nodes.all().aggregate(Max("data_updated"))
        input_nodes = self.workflow.nodes.filter(input_table__isnull=False).all()

        cache_key = get_cache_key(
            node_id=self.id,
            nodes_last_updated=str(nodes_last_updated["data_updated__max"]),
            input_tables=[node.input_table.cache_key for node in input_nodes],
        )

        if (res := cache.get(cache_key)) is None:
            res = get_query_from_node(self).schema()
            cache.set(cache_key, res, 30)

        return res

    @property
    def display_name(self):
        return NODE_CONFIG[self.kind]["displayName"]

    @property
    def icon(self):
        return NODE_CONFIG[self.kind]["icon"]

    @property
    def has_enough_parents(self):
        from apps.nodes.bigquery import (NODE_FROM_CONFIG,
                                         get_arity_from_node_func)

        func = NODE_FROM_CONFIG[self.kind]
        min_arity, _ = get_arity_from_node_func(func)
        return self.parents.count() >= min_arity

    def get_table_name(self):
        return f"Workflow:{self.workflow.name}:{self.output_name}"
