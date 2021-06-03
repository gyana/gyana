from functools import cached_property

from apps.tables.models import Table
from apps.utils.live_update_form import LiveUpdateForm
from apps.workflows.widgets import SourceSelect
from django import forms
from django.forms.models import BaseInlineFormSet
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput

# fmt: off
from .models import (AddColumn, Column, EditColumn, FunctionColumn, Node,
                     RenameColumn, SortColumn, Workflow)

# fmt: on


class WorkflowForm(forms.ModelForm):
    class Meta:
        model = Workflow
        fields = ["name", "project"]
        widgets = {"project": HiddenInput()}


class NodeForm(LiveUpdateForm):
    @cached_property
    def columns(self):
        """Returns the schema for the first parent."""
        return self.instance.parents.first().schema


class InputNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ["input_table"]
        labels = {"input_table": "Integration"}
        widgets = {"input_table": SourceSelect()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        self.fields["input_table"].queryset = Table.objects.filter(
            project=instance.workflow.project
        )


class OutputNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ["output_name"]
        labels = {"output_name": "Output name"}


class SelectNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["select_columns"] = forms.MultipleChoiceField(
            choices=[(col, col) for col in self.columns],
            widget=CheckboxSelectMultiple,
            initial=list(self.instance.columns.all().values_list("name", flat=True)),
        )

    def save(self, *args, **kwargs):
        self.instance.columns.all().delete()
        self.instance.columns.set(
            [Column(name=name) for name in self.cleaned_data["select_columns"]],
            bulk=False,
        )
        return super().save(*args, **kwargs)


class JoinNodeForm(NodeForm):
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
        self.form.base_fields["name"] = forms.ChoiceField(
            choices=[
                ("", "No column selected"),
                *[(col, col) for col in self.instance.parents.first().schema],
            ]
        )


NUMERIC_AGGREGATIONS = [
    FunctionColumn.Functions.COUNT,
    FunctionColumn.Functions.SUM,
    FunctionColumn.Functions.MEAN,
    FunctionColumn.Functions.MAX,
    FunctionColumn.Functions.MIN,
    FunctionColumn.Functions.STD,
]

AGGREGATION_TYPE_MAP = {
    "String": [FunctionColumn.Functions.COUNT],
    "Int64": NUMERIC_AGGREGATIONS,
    "Float64": NUMERIC_AGGREGATIONS,
}


class FunctionColumnForm(LiveUpdateForm):
    class Meta:
        fields = ("name", "function")

    @property
    def column_type(self):
        column = self.get_live_field("name")
        if column in self.schema:
            return self.schema[column].name
        return None

    def get_live_fields(self):
        fields = ["name"]

        if self.column_type is not None:
            fields += ["function"]

        return fields

    def __init__(self, *args, **kwargs):
        self.schema = kwargs.pop("schema")

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
    extra=1,
    can_delete=True,
    formset=InlineColumnFormset,
)

ColumnFormSet = forms.inlineformset_factory(
    Node,
    Column,
    fields=("name",),
    extra=1,
    can_delete=True,
    formset=InlineColumnFormset,
)


SortColumnFormSet = forms.inlineformset_factory(
    Node,
    SortColumn,
    fields=("name", "ascending"),
    can_delete=True,
    extra=1,
    formset=InlineColumnFormset,
)


IBIS_TO_PREFIX = {"String": "string_", "Int64": "integer_"}


class OperationColumnForm(LiveUpdateForm):
    class Meta:
        fields = (
            "name",
            "string_function",
            "integer_function",
        )

    def __init__(self, *args, **kwargs):

        self.schema = kwargs.pop("schema")

        super().__init__(*args, **kwargs)

    @property
    def column_type(self):
        column = self.get_live_field("name")
        if column in self.schema:
            return self.schema[column].name
        return None

    def get_live_fields(self):
        fields = ["name"]

        if self.column_type == "Int64":
            return fields + ["integer_function"]

        if self.column_type == "String":
            return fields + ["string_function"]

        return fields


EditColumnFormSet = forms.inlineformset_factory(
    Node,
    EditColumn,
    form=OperationColumnForm,
    can_delete=True,
    extra=1,
    formset=InlineColumnFormset,
)


class AddColumnForm(OperationColumnForm):
    class Meta:
        fields = ("name", "string_function", "integer_function", "label")

    def get_live_fields(self):
        fields = super().get_live_fields()

        if (
            self.get_live_field("integer_function")
            or self.get_live_field("string_function")
        ) is not None:
            return fields + ["label"]

        return fields


AddColumnFormSet = forms.inlineformset_factory(
    Node,
    AddColumn,
    form=AddColumnForm,
    can_delete=True,
    extra=1,
    formset=InlineColumnFormset,
)


RenameColumnFormSet = forms.inlineformset_factory(
    Node,
    RenameColumn,
    fields=("name", "new_name"),
    can_delete=True,
    extra=1,
    formset=InlineColumnFormset,
)


class UnionNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ["union_distinct"]
        labels = {"union_distinct": "distinct"}


class LimitNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ["limit_limit", "limit_offset"]
        labels = {"limit_limit": "Limit", "limit_offset": "Offset"}


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
}
KIND_TO_FORMSETS = {
    "aggregation": [FunctionColumnFormSet, ColumnFormSet],
    "sort": [SortColumnFormSet],
    "edit": [EditColumnFormSet],
    "add": [AddColumnFormSet],
    "rename": [RenameColumnFormSet],
}
