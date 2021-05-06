from apps.datasets.models import Dataset
from django import forms
from django.forms.widgets import HiddenInput

from .models import AGGREGATIONS, Aggregations, Dataflow, Groups, Node


class DataflowForm(forms.ModelForm):
    class Meta:
        model = Dataflow
        fields = ["name", "project"]
        widgets = {"project": HiddenInput()}


# Using a callable to refresh selection when a new dataset is added
def get_datasets():
    return ((d.id, d.name) for d in Dataset.objects.all())


class InputNode(forms.ModelForm):
    class Meta:
        model = Node
        fields = ["input_dataset"]
        labels = {"input_dataset": "Dataset"}


class JoinNode(forms.ModelForm):
    class Meta:
        model = Node
        fields = ["join_how", "join_left", "join_right"]
        labels = {"join_how": "How", "join_left": "Left", "join_right": "Right"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # https://stackoverflow.com/a/30766247/15425660
        node = self.instance
        self.left_columns = [(col, col) for col in node.parents.first().get_schema()]
        self.right_columns = [(col, col) for col in node.parents.last().get_schema()]
        self.fields["join_left"].choices = self.left_columns
        self.fields["join_right"].choices = self.right_columns


AggregationForms = forms.inlineformset_factory(
    Node, Aggregations, fields=("aggregation", "column")
)

GroupForms = forms.inlineformset_factory(Node, Groups, fields=("column",), extra=1)


KIND_TO_FORM = {"input": InputNode, "join": JoinNode}
