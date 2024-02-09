from crispy_forms.layout import Layout
from django import forms
from django.utils.functional import cached_property

from apps.base.core.utils import create_column_choices
from apps.base.crispy import CrispyFormset
from apps.base.forms import ModelForm
from apps.base.widgets import MultiSelect
from apps.columns.models import Column
from apps.tables.widgets import TableSelect

from .formsets import (
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


class NodeForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in getattr(self.Meta, "required", []):
            self.fields[field].required = True

    @cached_property
    def columns(self):
        """Returns the schema for the first parent."""
        parent = self.instance.parents.first()
        return parent.schema if parent else {}

    def save(self, commit=True):
        if not self.instance.has_been_saved:
            self.instance.has_been_saved = True
        return super().save(commit=commit)


class DefaultNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = []


class InputNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ["input_table"]
        labels = {"input_table": "Table"}
        widgets = {"input_table": TableSelect(parent="workflow")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["input_table"].widget.parent_entity = self.instance.workflow


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
        effect = (
            f"choices.pivot_aggregation = $store.ibis.aggregations[schema[pivot_value]]"
        )

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
        formsets = {
            "columns": UnpivotColumnFormSet,
            "secondary_columns": SelectColumnFormSet,
        }
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
            CrispyFormset("columns", "Unpivot columns"),
            CrispyFormset("secondary_columns", "Select columns"),
        )


class JoinNodeForm(DefaultNodeForm):
    class Meta:
        model = Node
        fields = []
        formsets = {"join_columns": JoinColumnFormset}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("join_columns", "Join columns"),
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
    class Meta:
        model = Node
        fields = []
        formsets = {"filters": FilterFormSet}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("filters", "Filters"),
        )


class EditColumnNodeForm(DefaultNodeForm):
    class Meta:
        model = Node
        fields = []
        formsets = {"edit_columns": EditColumnFormSet}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("edit_columns", "Edit columns"),
        )


class AddColumnNodeForm(DefaultNodeForm):
    class Meta:
        model = Node
        fields = []
        formsets = {"add_columns": AddColumnFormSet}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("add_columns", "Add columns"),
        )


class RenameColumnNodeForm(DefaultNodeForm):
    class Meta:
        model = Node
        fields = []
        formsets = {"rename_columns": RenameColumnFormSet}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("rename_columns", "Rename columns"),
        )


class SortColumnNodeForm(DefaultNodeForm):
    class Meta:
        model = Node
        fields = []
        formsets = {"sort_columns": SortColumnFormSet}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("sort_columns", "Sort columns"),
        )


class ConvertColumnNodeForm(DefaultNodeForm):
    class Meta:
        model = Node
        fields = []
        formsets = {"convert_columns": ConvertColumnFormSet}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("convert_columns", "Select columns to convert"),
        )


class FormulaColumnNodeForm(DefaultNodeForm):
    class Meta:
        model = Node
        fields = []
        formsets = {"formula_columns": FormulaColumnFormSet}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("formula_columns", "Formula columns"),
        )


class AggregateNodeForm(DefaultNodeForm):
    class Meta:
        model = Node
        fields = []
        formsets = {"columns": ColumnFormSet, "aggregations": AggregationColumnFormSet}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("columns", "Group columns"),
            CrispyFormset("aggregations", "Aggregations"),
        )


class WindowColumnNodeform(DefaultNodeForm):
    class Meta:
        model = Node
        fields = []
        formsets = {"window_columns": WindowColumnFormSet}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            CrispyFormset("window_columns", "Window columns"),
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
