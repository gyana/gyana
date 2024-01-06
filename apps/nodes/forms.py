from crispy_forms.layout import Layout
from django import forms
from django.utils.functional import cached_property

from apps.base.core.utils import create_column_choices
from apps.base.crispy import CrispyFormset
from apps.base.forms import (
    IntegrationSearchMixin,
    LiveAlpineModelForm,
    LiveFormsetMixin,
    SchemaFormMixin,
)
from apps.base.widgets import MultiSelect, SourceSelect
from apps.columns.models import Column

from .formsets import (
    KIND_TO_FORMSETS,
    AddColumnFormSet,
    AggregationColumnFormSet,
    ColumnFormSet,
    ConvertColumnFormSet,
    EditColumnFormSet,
    FilterFormSet,
    FormulaColumnFormSet,
    JoinColumnFormset,
    RenameColumnFormSet,
    SelectColumnFormSet,
    SortColumnFormSet,
    UnpivotColumnFormSet,
    WindowColumnFormSet,
)
from .models import Node


class NodeForm(LiveFormsetMixin, SchemaFormMixin, LiveAlpineModelForm):
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


class InputNodeForm(IntegrationSearchMixin, NodeForm):
    search = forms.CharField(required=False)

    class Meta:
        model = Node
        fields = ["input_table"]
        labels = {"input_table": "Table"}
        widgets = {"input_table": SourceSelect()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "search" in self.fields:
            self.order_fields(["search", "input_table"])
            self.fields["search"].widget.attrs["data-action"] = "input->tf-modal#search"

            # Re-focus the search bar when there is a value
            if self.data.get("search"):
                self.fields["search"].widget.attrs["autofocus"] = ""

            self.search_queryset(
                self.fields["input_table"],
                self.instance.workflow.project,
                self.instance.input_table,
                self.instance.workflow.input_tables_fk,
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
        show = {
            "pivot_aggregation": "pivot_value !== null",
        }
        effect = {
            "pivot_value": f"choices.pivot_aggregation = $store.ibis.aggregations[schema[pivot_value]]"
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

        self.helper.layout = Layout(
            "unpivot_value",
            "unpivot_column",
            CrispyFormset("unpivot", "Unpivot columns", UnpivotColumnFormSet),
            CrispyFormset("select", "Select columns", SelectColumnFormSet),
        )


class JoinNodeForm(DefaultNodeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("joins", "Join columns", JoinColumnFormset),
        )

    def get_formset_kwargs(self, formset):
        parents_count = self.instance.parents.count()
        names = [f"Join Input {i+2}" for i in range(parents_count)]
        return {
            "max_num": parents_count - 1,
            "min_num": parents_count - 1,
            "names": names,
        }


class FilterNodeForm(DefaultNodeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("filter", "Filters", FilterFormSet),
        )


class EditColumnNodeForm(DefaultNodeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("edit", "Edit columns", EditColumnFormSet),
        )


class AddColumnNodeForm(DefaultNodeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("add", "Add columns", AddColumnFormSet),
        )


class RenameColumnNodeForm(DefaultNodeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("rename", "Rename columns", RenameColumnFormSet),
        )


class SortColumnNodeForm(DefaultNodeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("sort", "Sort columns", SortColumnFormSet),
        )


class ConvertColumnNodeForm(DefaultNodeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("convert", "Select columns to convert", ConvertColumnFormSet),
        )


class FormulaColumnNodeForm(DefaultNodeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("formula", "Formula columns", FormulaColumnFormSet),
        )


class AggregateNodeForm(DefaultNodeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("group", "Group columns", ColumnFormSet),
            CrispyFormset("aggregrate", "Aggregations", AggregationColumnFormSet),
        )


class WindowColumnNodeform(DefaultNodeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("window", "Window columns", WindowColumnFormSet),
        )


KIND_TO_FORM = {
    "input": InputNodeForm,
    "output": OutputNodeForm,
    "select": SelectNodeForm,
    "except": DefaultNodeForm,
    "join": JoinNodeForm,
    "aggregation": AggregateNodeForm,
    "union": UnionNodeForm,
    "sort": SortColumnNodeForm,
    "limit": LimitNodeForm,
    # Is defined in the filter app and will be rendered via a
    # different htmx partial
    "filter": FilterNodeForm,
    "edit": EditColumnNodeForm,
    "add": AddColumnNodeForm,
    "rename": RenameColumnNodeForm,
    "formula": FormulaColumnNodeForm,
    "distinct": DistinctNodeForm,
    "pivot": PivotNodeForm,
    "unpivot": UnpivotNodeForm,
    "intersect": DefaultNodeForm,
    "window": WindowColumnNodeform,
    "convert": ConvertColumnNodeForm,
}
