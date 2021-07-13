from functools import cached_property

from apps.filters.forms import FilterForm
from apps.filters.models import Filter
from apps.tables.models import Table
from apps.utils.live_update_form import LiveUpdateForm
from apps.utils.schema_form_mixin import SchemaFormMixin
from apps.workflows.nodes import AllOperations
from apps.workflows.widgets import CodeMirror, InputNode, MultiSelect
from django import forms
from django.forms.models import BaseInlineFormSet
from django.forms.widgets import HiddenInput

# fmt: off
from .models import (AddColumn, AggregationFunctions, Column, EditColumn,
                     FormulaColumn, FunctionColumn, Node, RenameColumn,
                     SecondaryColumn, SortColumn, WindowColumn, Workflow)

# fmt: on


class WorkflowFormCreate(forms.ModelForm):
    class Meta:
        model = Workflow
        fields = ["project"]
        widgets = {"project": HiddenInput()}


class WorkflowForm(forms.ModelForm):
    class Meta:
        model = Workflow
        fields = ["name"]


class NodeForm(LiveUpdateForm):
    @cached_property
    def columns(self):
        """Returns the schema for the first parent."""
        return self.instance.parents.first().schema


class InputNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ["input_table"]
        labels = {"input_table": "Select an integration to get data from:"}
        widgets = {"input_table": InputNode()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        self.fields["input_table"].queryset = Table.objects.filter(
            project=instance.workflow.project
        ).exclude(source="intermediate_node")


class OutputNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ["output_name"]
        labels = {"output_name": "Output name"}


class SelectNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ("select_mode",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["select_columns"] = forms.MultipleChoiceField(
            choices=[(col, col) for col in self.columns],
            widget=MultiSelect,
            label="Select the columns you want to use:",
            initial=list(self.instance.columns.all().values_list("column", flat=True)),
        )

    def save(self, *args, **kwargs):
        self.instance.columns.all().delete()
        self.instance.columns.set(
            [Column(column=column) for column in self.cleaned_data["select_columns"]],
            bulk=False,
        )
        return super().save(*args, **kwargs)


class JoinNodeForm(NodeForm):
    join_left = forms.ChoiceField(
        choices=(),
    )
    join_right = forms.ChoiceField(
        choices=(),
    )

    class Meta:
        model = Node
        fields = ["join_how", "join_left", "join_right"]
        labels = {"join_how": "How", "join_left": "Left", "join_right": "Right"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # https://stackoverflow.com/a/30766247/15425660
        node = self.instance
        self.left_columns = [(col, col) for col in node.parents.first().schema]
        self.right_columns = [(col, col) for col in node.parents.last().schema]
        self.fields["join_left"].choices = self.left_columns
        self.fields["join_right"].choices = self.right_columns


class InlineColumnFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.form.base_fields["column"] = forms.ChoiceField(
            choices=[
                ("", "No column selected"),
                *[(col, col) for col in self.instance.parents.first().schema],
            ]
        )


NUMERIC_AGGREGATIONS = [
    AggregationFunctions.COUNT,
    AggregationFunctions.SUM,
    AggregationFunctions.MEAN,
    AggregationFunctions.MAX,
    AggregationFunctions.MIN,
    AggregationFunctions.STD,
]

AGGREGATION_TYPE_MAP = {
    "String": [AggregationFunctions.COUNT],
    "Int64": NUMERIC_AGGREGATIONS,
    "Float64": NUMERIC_AGGREGATIONS,
}


class FunctionColumnForm(SchemaFormMixin, LiveUpdateForm):
    class Meta:
        fields = ("column", "function")

    def get_live_fields(self):
        fields = ["column"]

        if self.column_type is not None:
            fields += ["function"]

        return fields

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if self.column_type is not None:
            self.fields["function"].choices = [
                (choice.value, choice.name)
                for choice in AGGREGATION_TYPE_MAP[self.column_type]
            ]


FunctionColumnFormSet = forms.inlineformset_factory(
    Node,
    FunctionColumn,
    form=FunctionColumnForm,
    extra=0,
    can_delete=True,
    formset=InlineColumnFormset,
)

ColumnFormSet = forms.inlineformset_factory(
    Node,
    Column,
    fields=("column",),
    extra=0,
    can_delete=True,
    formset=InlineColumnFormset,
)


SortColumnFormSet = forms.inlineformset_factory(
    Node,
    SortColumn,
    fields=("column", "ascending"),
    can_delete=True,
    extra=0,
    formset=InlineColumnFormset,
)


IBIS_TO_FUNCTION = {
    "String": "string_function",
    "Int64": "integer_function",
    "Float64": "integer_function",
    "Timestamp": "datetime_function",
    "Date": "date_function",
    "Time": "time_function",
}


class OperationColumnForm(SchemaFormMixin, LiveUpdateForm):
    class Meta:
        fields = (
            "column",
            "string_function",
            "integer_function",
            "date_function",
            "time_function",
            "datetime_function",
            "integer_value",
            "float_value",
            "string_value",
        )

    def get_live_fields(self):
        fields = ["column"]

        if self.column_type and (function_field := IBIS_TO_FUNCTION[self.column_type]):
            fields += [function_field]
            operation = AllOperations.get(self.get_live_field(function_field))
            if operation and operation.arguments == 1:
                fields += [operation.value_field]

        return fields

    def save(self, commit: bool):
        # Make sure only one function is set and turn the others to Null
        for field in self.base_fields:
            if field.endswith("function") and f"{self.prefix}-{field}" not in self.data:
                setattr(self.instance, field, None)
        return super().save(commit=commit)


EditColumnFormSet = forms.inlineformset_factory(
    Node,
    EditColumn,
    form=OperationColumnForm,
    can_delete=True,
    extra=0,
    formset=InlineColumnFormset,
)


class AddColumnForm(SchemaFormMixin, LiveUpdateForm):
    class Meta:
        fields = (
            "column",
            "string_function",
            "integer_function",
            "date_function",
            "time_function",
            "datetime_function",
            "integer_value",
            "float_value",
            "string_value",
            "label",
        )

    def get_live_fields(self):
        fields = ["column"]

        if self.column_type == "Int64":
            fields += ["integer_function"]

            if self.get_live_field("integer_function") is not None:
                fields += ["label"]

        elif self.column_type == "String":
            fields += ["string_function"]

            if self.get_live_field("string_function") is not None:
                fields += ["label"]

        return fields


AddColumnFormSet = forms.inlineformset_factory(
    Node,
    AddColumn,
    form=AddColumnForm,
    can_delete=True,
    extra=0,
    formset=InlineColumnFormset,
)


class FormulaColumnForm(SchemaFormMixin, LiveUpdateForm):
    class Meta:
        fields = ("formula", "label")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["formula"].widget = CodeMirror(self.schema)


FormulaColumnFormSet = forms.inlineformset_factory(
    Node,
    FormulaColumn,
    form=FormulaColumnForm,
    fields=("formula", "label"),
    can_delete=True,
    extra=0,
)

RenameColumnFormSet = forms.inlineformset_factory(
    Node,
    RenameColumn,
    fields=("column", "new_name"),
    can_delete=True,
    extra=0,
    formset=InlineColumnFormset,
)

FilterFormSet = forms.inlineformset_factory(
    Node, Filter, form=FilterForm, can_delete=True, extra=0
)


class UnionNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = [
            "union_mode",
            "union_distinct",
        ]
        labels = {"union_distinct": "distinct", "union_mode": "mode"}


class LimitNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ["limit_limit", "limit_offset"]
        labels = {"limit_limit": "Limit", "limit_offset": "Offset"}


# TODO: Use Nodeform instead
class PivotNodeForm(LiveUpdateForm):
    class Meta:
        model = Node
        fields = ["pivot_index", "pivot_column", "pivot_value", "pivot_aggregation"]
        # TODO: Add labels

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        schema = self.instance.parents.first().schema
        column_choices = [
            ("", "No column selected"),
            *[(col, col) for col in schema],
        ]
        self.fields["pivot_index"] = forms.ChoiceField(
            choices=column_choices, required=False
        )
        self.fields["pivot_column"] = forms.ChoiceField(choices=column_choices)
        self.fields["pivot_value"] = forms.ChoiceField(choices=column_choices)

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


class UnpivotNodeForm(LiveUpdateForm):
    class Meta:
        model = Node
        fields = ["unpivot_value", "unpivot_column"]


SelectColumnFormSet = forms.inlineformset_factory(
    Node,
    SecondaryColumn,
    fields=("column",),
    can_delete=True,
    extra=0,
    formset=InlineColumnFormset,
)

UnpivotColumnFormSet = forms.inlineformset_factory(
    Node,
    Column,
    fields=("column",),
    can_delete=True,
    extra=0,
    formset=InlineColumnFormset,
)


class WindowForm(SchemaFormMixin, LiveUpdateForm):
    class Meta:
        fields = ("column", "function", "group_by", "order_by", "ascending", "label")
        model = WindowColumn

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        column_field = forms.ChoiceField(
            choices=[
                ("", "No column selected"),
                *[(col, col) for col in self.schema],
            ]
        )
        self.fields["column"] = column_field
        if self.column_type is not None:
            self.fields["function"].choices = [
                (choice.value, choice.name)
                for choice in AGGREGATION_TYPE_MAP[self.column_type]
            ]
            self.fields["group_by"] = column_field
            self.fields["order_by"] = column_field

    def get_live_fields(self):
        fields = ["column"]

        if self.column_type is not None:
            fields += ["function", "group_by", "order_by", "ascending", "label"]

        return fields


WindowColumnFormSet = forms.inlineformset_factory(
    Node, WindowColumn, can_delete=True, extra=True, form=WindowForm
)


class DefaultNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = []


KIND_TO_FORM = {
    "input": InputNodeForm,
    "output": OutputNodeForm,
    "select": SelectNodeForm,
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
    "distinct": SelectNodeForm,
    "pivot": PivotNodeForm,
    "unpivot": UnpivotNodeForm,
    "intersect": DefaultNodeForm,
    "window": DefaultNodeForm,
}

KIND_TO_FORMSETS = {
    "aggregation": [FunctionColumnFormSet, ColumnFormSet],
    "sort": [SortColumnFormSet],
    "edit": [EditColumnFormSet],
    "add": [AddColumnFormSet],
    "rename": [RenameColumnFormSet],
    "filter": [FilterFormSet],
    "formula": [FormulaColumnFormSet],
    "unpivot": [UnpivotColumnFormSet, SelectColumnFormSet],
    "window": [WindowColumnFormSet],
}
