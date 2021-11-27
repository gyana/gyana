from dirtyfields import DirtyFieldsMixin
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from model_clone import CloneMixin

from apps.base.aggregations import AggregationFunctions
from apps.base.models import BaseModel
from apps.nodes.config import NODE_CONFIG
from apps.tables.models import Table
from apps.workflows.models import Workflow


class Node(DirtyFieldsMixin, CloneMixin, BaseModel):
    class Meta:
        ordering = ()

    class Kind(models.TextChoices):
        ADD = "add", "Add"
        AGGREGATION = "aggregation", "Group and Aggregate"
        CONVERT = "convert", "Convert"
        DISTINCT = "distinct", "Distinct"
        EDIT = "edit", "Edit"
        FILTER = "filter", "Filter"
        INPUT = "input", "Get data"
        FORMULA = "formula", "Formula"
        INTERSECT = "intersect", "Intersect "
        JOIN = "join", "Join"
        LIMIT = "limit", "Limit"
        PIVOT = "pivot", "Pivot"
        OUTPUT = "output", "Save data"
        RENAME = "rename", "Rename"
        SELECT = "select", "Select columns"
        SORT = "sort", "Sort"
        UNION = "union", "Union"
        EXCEPT = "except", "Except"
        UNPIVOT = "unpivot", "Unpivot"
        TEXT = "text", "Text"
        WINDOW = "window", "Window and Calculate"
        SENTIMENT = "sentiment", "Sentiment"

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
        "convert_columns",
    ]

    workflow = models.ForeignKey(
        Workflow, on_delete=models.CASCADE, related_name="nodes"
    )
    name = models.CharField(max_length=64, null=True, blank=True)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    x = models.FloatField()
    y = models.FloatField()
    parents = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        through="Edge",
        through_fields=["child", "parent"],
    )

    data_updated = models.DateTimeField(null=True, editable=False)

    error = models.CharField(max_length=300, null=True)
    intermediate_table = models.ForeignKey(
        Table, on_delete=models.CASCADE, null=True, related_name="intermediate_table"
    )
    cache_table = models.ForeignKey(
        Table, on_delete=models.CASCADE, null=True, related_name="cache_table"
    )
    # ======== Node specific columns ========= #

    # Input
    input_table = models.ForeignKey(
        Table, on_delete=models.SET_NULL, null=True, help_text="Select a data source"
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
    # aggregations exists on AggregationColumn as FK

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

    # Union/Except
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
        null=True, blank=True, help_text="From where to start the limit"
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
    sentiment_column = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        null=True,
        blank=True,
        help_text="Select the text column to get the sentiment of.",
    )

    # Credits
    always_use_credits = models.BooleanField(default=False)
    uses_credits = models.IntegerField(default=0)
    credit_use_confirmed = models.DateTimeField(null=True, editable=False)
    # To know who spent credits without having a global user session item or
    # pass down the user through multiple functions we persist it in the database
    credit_confirmed_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )

    has_been_saved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        dirty_fields = set(self.get_dirty_fields(check_relationship=True).keys()) - {
            "name",
            "x",
            "y",
            "error",
            "always_use_credits",
            "uses_credits",
            "credit_use_confirmed",
            "credit_confirmed_user",
        }
        if dirty_fields:
            self.workflow.data_updated = timezone.now()
            self.workflow.save()
        if dirty_fields and "data_updated" not in dirty_fields:
            self.data_updated = timezone.now()

        return super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return self.has_been_saved or self.kind not in [
            self.Kind.INPUT,
            self.Kind.SENTIMENT,
            self.Kind.JOIN,
            self.Kind.PIVOT,
            self.Kind.UNPIVOT,
        ]

    @cached_property
    def schema(self):

        from .bigquery import get_query_from_node

        query = get_query_from_node(self)
        return query.schema()

    @property
    def display_name(self):
        return NODE_CONFIG[self.kind]["displayName"]

    @property
    def icon(self):
        return NODE_CONFIG[self.kind]["icon"]

    @property
    def has_enough_parents(self):
        from apps.nodes.bigquery import NODE_FROM_CONFIG, get_arity_from_node_func

        func = NODE_FROM_CONFIG[self.kind]
        min_arity, _ = get_arity_from_node_func(func)
        return self.parents.count() >= min_arity

    def get_table_name(self):
        return f"Workflow:{self.workflow.name}:{self.name}"

    @property
    def bq_output_table_id(self):
        return f"output_node_{self.id:09}"

    @property
    def bq_intermediate_table_id(self):
        return f"intermediate_node_{self.id:09}"

    @property
    def bq_cache_table_id(self):
        return f"cache_node_{self.id:09}"

    @property
    def explanation(self):
        return NODE_CONFIG[self.kind]["explanation"]

    @property
    def parents_ordered(self):
        return self.parents.order_by("child_edges")


class Edge(models.Model):
    class Meta:
        unique_together = ("child", "position")
        ordering = ("position",)

    child = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="parent_edges"
    )
    parent = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="child_edges"
    )
    position = models.IntegerField(default=0)
