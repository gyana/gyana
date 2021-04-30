from apps.datasets.models import Dataset
from django import forms

from .models import Dataflow


class DataflowForm(forms.ModelForm):
    class Meta:
        model = Dataflow
        fields = ["name"]


# Using a callable to refresh selection when a new dataset is added
def get_datasets():
    return ((d.id, d.name) for d in Dataset.objects.all())


class InputNode(forms.Form):
    dataset = forms.ChoiceField(
        choices=get_datasets,
    )


class PivotNode(forms.Form):
    index = forms.CharField()
    columns = forms.CharField()
    values = forms.CharField()


class UnpivotNode(forms.Form):
    id_vars = forms.CharField()
    value_vars = forms.CharField()


KIND_TO_FORM = {"pivot": PivotNode, "unpivot": UnpivotNode, "input": InputNode}
