from apps.datasets.models import Dataset
from django import forms

from .models import Dataflow, Node


class DataflowForm(forms.ModelForm):
    class Meta:
        model = Dataflow
        fields = ["name"]


# Using a callable to refresh selection when a new dataset is added
def get_datasets():
    return ((d.id, d.name) for d in Dataset.objects.all())


class InputNode(forms.ModelForm):
    class Meta:
        model = Node
        fields = ["_input_dataset"]
        labels = {"_input_dataset": "Dataset"}


KIND_TO_FORM = {"input": InputNode}
