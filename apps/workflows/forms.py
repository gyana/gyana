from functools import cached_property

from apps.tables.models import Table
from django import forms
from django.forms.models import BaseInlineFormSet
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput

from .models import Column, FunctionColumn, Node, SortColumn, Workflow


class WorkflowForm(forms.ModelForm):
    class Meta:
        model = Workflow
        fields = ["name", "project"]
        widgets = {"project": HiddenInput()}


class NodeForm(forms.ModelForm):
    @cached_property
    def columns(self):
        """Returns the schema for the first parent."""
        return self.instance.parents.first().schema


class InputNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = ["input_table"]
        labels = {"input_table": "Integration"}

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


FunctionColumnFormSet = forms.inlineformset_factory(
    Node,
    FunctionColumn,
    fields=("name", "function"),
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


class GroupNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = []


SortColumnFormSet = forms.inlineformset_factory(
    Node,
    SortColumn,
    fields=("name", "ascending"),
    can_delete=True,
    extra=1,
    formset=InlineColumnFormset,
)


class SortNodeForm(NodeForm):
    class Meta:
        model = Node
        fields = []


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
    "aggregation": GroupNodeForm,
    "union": UnionNodeForm,
    "sort": SortNodeForm,
    "limit": LimitNodeForm,
    # Is defined in the filter app and will be rendered via a
    # different turbo frame
    "filter": DefaultNodeForm,
}
KIND_TO_FORMSETS = {
    "aggregation": [FunctionColumnFormSet, ColumnFormSet],
    "sort": [SortColumnFormSet],
}
