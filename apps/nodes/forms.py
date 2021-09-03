from functools import cached_property

from apps.base.live_update_form import LiveUpdateForm
from apps.columns.forms import AGGREGATION_TYPE_MAP
from apps.columns.models import Column
from apps.nodes.formsets import KIND_TO_FORMSETS
from apps.tables.models import Table
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
        self.fields["input_table"].queryset = Table.available.filter(
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
        self.instance.columns.set(
            [Column(column=column) for column in self.cleaned_data["distinct_columns"]],
            bulk=False,
        )
        return super().save(*args, **kwargs)


class JoinNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ["join_how", "join_left", "join_right"]
        labels = {"join_how": "How", "join_left": "Left", "join_right": "Right"}
        required = ["join_how", "join_left", "join_right"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["join_left"] = forms.ChoiceField(
            choices=[
                ("", "No column selected"),
                *[(col, col) for col in self.instance.parents.first().schema],
            ],
            help_text=self.fields["join_left"].help_text,
        )
        self.fields["join_right"] = forms.ChoiceField(
            choices=[
                ("", "No column selected"),
                *[(col, col) for col in self.instance.parents.last().schema],
            ],
            help_text=self.fields["join_right"].help_text,
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
        column_choices = [
            ("", "No column selected"),
            *[(col, col) for col in schema],
        ]
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


class SentimenttNodeForm(NodeForm):
    sentiment_column = forms.ChoiceField(
        choices=(),
    )

    class Meta:
        model = Node
        fields = ("sentiment_column",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sentiment_column"].choices = [
            (name, name)
            for name, type_ in self.columns.items()
            if type_.name == "String"
        ]


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
    "distinct": DistinctNodeForm,
    "pivot": PivotNodeForm,
    "unpivot": UnpivotNodeForm,
    "intersect": DefaultNodeForm,
    "sentiment": SentimenttNodeForm,
    "window": DefaultNodeForm,
}
