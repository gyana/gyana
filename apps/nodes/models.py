from itertools import chain

from dirtyfields import DirtyFieldsMixin
from django.conf import settings
from django.db import models
from django.urls.base import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from apps.base.core.aggregations import AggregationFunctions
from apps.base.models import BaseModel
from apps.dashboards.models import Dashboard
from apps.nodes.clone import clone_tables
from apps.nodes.config import NODE_CONFIG
from apps.tables.models import Table
from apps.workflows.models import Workflow


class Node(DirtyFieldsMixin, BaseModel):
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

    _clone_excluded_m2m_fields = ["parents", "node_set"]
    _clone_excluded_m2o_or_o2m_fields = [
        "parent_edges",
        "child_edges",
        "input_table",
    ]
    _clone_excluded_o2o_fields = ["table", "intermediate_table", "cache_table"]

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

    # ======== Node specific columns ========= #

    # Input
    input_table = models.ForeignKey(
        Table,
        on_delete=models.SET_NULL,
        null=True,
        related_name="input_nodes",
        help_text="Select a table from an integration or workflow",
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
    # See JoinColumn

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

    has_been_saved = models.BooleanField(default=False)

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

    @property
    def is_valid(self):
        return self.has_been_saved or self.kind not in [
            self.Kind.INPUT,
            self.Kind.JOIN,
            self.Kind.PIVOT,
            self.Kind.UNPIVOT,
        ]

    @cached_property
    def schema(self):
        from .engine import get_query_from_node

        query = get_query_from_node(self)
        return query.schema

    @property
    def display_name(self):
        return NODE_CONFIG[self.kind]["displayName"]

    @property
    def icon(self):
        return NODE_CONFIG[self.kind]["icon"]

    @property
    def has_enough_parents(self):
        from apps.nodes.engine import NODE_FROM_CONFIG, get_arity_from_node_func

        func = NODE_FROM_CONFIG[self.kind]
        min_arity, _ = get_arity_from_node_func(func)

        return self.parents.count() >= min_arity and (
            self.kind != self.Kind.JOIN or self.join_is_valid
        )

    @property
    def join_is_valid(self):
        if self.kind == self.Kind.JOIN:
            join_count = self.join_columns.count()
            parents = self.parent_edges.all()
            positions = {p.position for p in parents[:join_count]}
            missing = set(range(join_count)).difference(positions)
            return len(parents) > 1 and not missing
        return False

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
        return self.parents.order_by("child_edges").cache()

    def get_absolute_url(self):
        workflow = self.workflow
        project = self.workflow.project
        return f'{reverse("project_workflows:detail", args=(project.id,workflow.id,))}?modal_item={self.id}'

    @property
    def used_in_workflows(self):
        return (
            Workflow.objects.filter(nodes__input_table__workflow_node=self)
            .distinct()
            .only("name", "project", "created", "updated")
            .annotate(kind=models.Value("Workflow", output_field=models.CharField()))
        )

    @property
    def used_in_dashboards(self):
        return (
            Dashboard.objects.filter(pages__widgets__table__workflow_node=self)
            .distinct()
            .only("name", "project", "created", "updated")
            .annotate(kind=models.Value("Dashboard", output_field=models.CharField()))
        )

    @property
    def used_in(self):
        return list(chain(self.used_in_workflows, self.used_in_dashboards))

    def make_clone(self, attrs=None, sub_clone=False, using=None):
        clone = super().make_clone(attrs=attrs, sub_clone=sub_clone, using=using)
        clone_tables(self, clone, using)
        return clone


class Edge(BaseModel):
    class Meta:
        unique_together = ("child", "position")
        ordering = ("position",)

    def save(self, *args, **kwargs):
        self.child.data_updated = timezone.now()
        self.child.save()
        return super().save(*args, **kwargs)

    child = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="parent_edges"
    )
    parent = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="child_edges"
    )
    position = models.IntegerField(default=0)
