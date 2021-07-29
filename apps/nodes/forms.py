from functools import cached_property

from apps.columns.forms import AGGREGATION_TYPE_MAP
from apps.columns.models import Column
from apps.nodes.formsets import KIND_TO_FORMSETS
from apps.tables.models import Table
from apps.utils.live_update_form import LiveUpdateForm
from django import forms

from .models import Node
from .widgets import InputNode, MultiSelect


class NodeForm(LiveUpdateForm):
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


class DefaultNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = []


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
        required = ["output_name"]


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
        required = ["join_how", "join_left", "join_right"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # https://stackoverflow.com/a/30766247/15425660
        node = self.instance
        self.left_columns = [(col, col) for col in node.parents.first().schema]
        self.right_columns = [(col, col) for col in node.parents.last().schema]
        self.fields["join_left"].choices = self.left_columns
        self.fields["join_right"].choices = self.right_columns


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
        required = ["unpivot_value", "unpivot_column"]


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
