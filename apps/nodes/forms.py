from django import forms
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Case, Q, When
from django.db.models.functions import Greatest
from django.forms.widgets import HiddenInput
from django.utils.functional import cached_property

from apps.base.core.utils import create_column_choices
from apps.base.forms import LiveFormsetForm
from apps.base.widgets import MultiSelect, SourceSelect
from apps.columns.forms import AGGREGATION_TYPE_MAP
from apps.columns.models import Column
from apps.nodes.formsets import KIND_TO_FORMSETS
from apps.tables.models import Table

from .models import Node

INPUT_SEARCH_THRESHOLD = 0.3


class NodeForm(LiveFormsetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in getattr(self.Meta, "required", []):
            self.fields[field].required = True

    @cached_property
    def columns(self):
        """Returns the schema for the first parent."""
        parent = self.instance.parents.first()
        return parent.schema if parent else {}

    def get_live_formsets(self):
        return KIND_TO_FORMSETS.get(self.instance.kind, [])

    def save(self, commit=True):
        if not self.instance.has_been_saved:
            self.instance.has_been_saved = True
        return super().save(commit=commit)


class DefaultNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = []


class InputNodeForm(NodeForm):
    search = forms.CharField(required=False)

    class Meta:
        model = Node
        fields = ["input_table"]
        labels = {"input_table": "Table"}
        widgets = {"input_table": SourceSelect()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.order_fields(["search", "input_table"])
        self.fields["search"].widget.attrs["data-action"] = "input->tf-modal#search"

        # Re-focus the search bar when there is a value
        if self.data.get("search"):
            self.fields["search"].widget.attrs["autofocus"] = ""

        self.fields["input_table"].queryset = (
            Table.available.filter(project=self.instance.workflow.project)
            .exclude(
                source__in=[Table.Source.INTERMEDIATE_NODE, Table.Source.CACHE_NODE]
            )
            .annotate(
                is_used_in=Case(
                    When(id__in=self.instance.workflow.input_tables_fk, then=True),
                    default=False,
                ),
            )
            .order_by("updated")
        )

        if search := self.data.get("search"):
            self.fields["input_table"].queryset = (
                self.fields["input_table"]
                .queryset.annotate(
                    similarity=Greatest(
                        TrigramSimilarity("integration__name", search),
                        TrigramSimilarity("workflow_node__workflow__name", search),
                        TrigramSimilarity("bq_table", search),
                    )
                )
                .filter(
                    Q(similarity__gte=INPUT_SEARCH_THRESHOLD)
                    | Q(id=getattr(self.instance.input_table, "id", None))
                )
                .order_by("-similarity")
            )


class OutputNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ["name"]
        labels = {"name": "Output name"}
        required = ["name"]
        help_texts = {
            "name": "Name your output, this name will be refered to in other workflows or dashboards.",
        }


class SelectNodeForm(NodeForm):

    select_columns = forms.MultipleChoiceField(
        choices=(),
        widget=MultiSelect,
        label="Select the columns you want to use:",
    )

    class Meta:
        model = Node
        fields = ("select_mode",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["select_columns"].initial = list(
            self.instance.columns.all().values_list("column", flat=True)
        )
        self.fields["select_columns"].choices = [(col, col) for col in self.columns]

    def save(self, *args, **kwargs):
        self.instance.columns.all().delete()
        self.instance.columns.add(
            *[Column(column=column) for column in self.cleaned_data["select_columns"]],
            bulk=False,
        )
        return super().save(*args, **kwargs)


class DistinctNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["distinct_columns"] = forms.MultipleChoiceField(
            choices=[(col, col) for col in self.columns],
            widget=MultiSelect,
            label="Select the columns that should be unique:",
            initial=list(self.instance.columns.all().values_list("column", flat=True)),
        )

    def save(self, *args, **kwargs):
        self.instance.columns.all().delete()
        self.instance.columns.add(
            *[
                Column(column=column)
                for column in self.cleaned_data["distinct_columns"]
            ],
            bulk=False,
        )
        return super().save(*args, **kwargs)


class UnionNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = [
            "union_distinct",
        ]
        labels = {"union_distinct": "distinct"}


class LimitNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ["limit_limit", "limit_offset"]
        labels = {"limit_limit": "Limit", "limit_offset": "Offset"}


# TODO: Use Nodeform instead
class PivotNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ["pivot_index", "pivot_column", "pivot_value", "pivot_aggregation"]
        labels = {
            "pivot_index": "Index column",
            "pivot_value": "Value column",
            "pivot_aggregation": "Aggregation function",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        schema = self.instance.parents.first().schema
        column_choices = create_column_choices(schema)

        self.fields["pivot_index"] = forms.ChoiceField(
            choices=column_choices,
            required=False,
            help_text=self.fields["pivot_index"].help_text,
        )
        self.fields["pivot_column"] = forms.ChoiceField(
            choices=column_choices, help_text=self.fields["pivot_column"].help_text
        )
        self.fields["pivot_value"] = forms.ChoiceField(
            choices=column_choices, help_text=self.fields["pivot_value"].help_text
        )

        pivot_value = self.get_live_field("pivot_value")
        if pivot_value in schema:
            column_type = schema[pivot_value].name

            self.fields["pivot_aggregation"].choices = [
                (choice.value, choice.name)
                for choice in AGGREGATION_TYPE_MAP[column_type]
            ]

    def get_live_fields(self):
        fields = ["pivot_index", "pivot_column", "pivot_value"]
        if self.get_live_field("pivot_value") is not None:
            fields += ["pivot_aggregation"]
        return fields


class UnpivotNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ["unpivot_value", "unpivot_column"]
        required = ["unpivot_value", "unpivot_column"]
        labels = {
            "unpivot_value": "Value column name",
            "unpivot_column": "Category column name",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_description = "Transform multiple columns into a single column."


class SentimentNodeForm(NodeForm):
    sentiment_column = forms.ChoiceField(
        choices=(),
    )

    class Meta:
        model = Node
        fields = ("sentiment_column", "always_use_credits", "credit_confirmed_user")
        widgets = {"credit_confirmed_user": HiddenInput()}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["sentiment_column"].choices = create_column_choices(
            [name for name, type_ in self.columns.items() if type_.name == "String"]
        )

    def get_initial_for_field(self, field, field_name):
        if field_name == "credit_confirmed_user":
            return self.user
        return super().get_initial_for_field(field, field_name)


class ExceptNodeForm(DefaultNodeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_description = "Remove rows that exist in a second table."


class JoinNodeForm(DefaultNodeForm):
    def get_formset_kwargs(self, formset):
        parents_count = self.instance.parents.count()
        names = [f"Join Input {i+2}" for i in range(parents_count)]
        return {
            "max_num": parents_count - 1,
            "min_num": parents_count - 1,
            "names": names,
        }


KIND_TO_FORM = {
    "input": InputNodeForm,
    "output": OutputNodeForm,
    "select": SelectNodeForm,
    "except": ExceptNodeForm,
    "join": JoinNodeForm,
    "aggregation": DefaultNodeForm,
    "union": UnionNodeForm,
    "sort": DefaultNodeForm,
    "limit": LimitNodeForm,
    # Is defined in the filter app and will be rendered via a
    # different turbo frame
    "filter": DefaultNodeForm,
    "edit": DefaultNodeForm,
    "add": DefaultNodeForm,
    "rename": DefaultNodeForm,
    "formula": DefaultNodeForm,
    "distinct": DistinctNodeForm,
    "pivot": PivotNodeForm,
    "unpivot": UnpivotNodeForm,
    "intersect": DefaultNodeForm,
    "sentiment": SentimentNodeForm,
    "window": DefaultNodeForm,
    "convert": DefaultNodeForm,
}
