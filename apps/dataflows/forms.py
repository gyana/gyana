from apps.datasets.models import Dataset
from apps.utils.formset_layout import Formset
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput, Select

from .models import Column, Dataflow, FunctionColumn, Node


class DataflowForm(forms.ModelForm):
    class Meta:
        model = Dataflow
        fields = ["name", "project"]
        widgets = {"project": HiddenInput()}


# Using a callable to refresh selection when a new dataset is added
def get_datasets():
    return ((d.id, d.name) for d in Dataset.objects.all())


class InputNodeForm(forms.ModelForm):
    class Meta:
        model = Node
        fields = ["input_dataset"]
        labels = {"input_dataset": "Dataset"}


class SelectNodeForm(forms.ModelForm):
    class Meta:
        model = Node
        fields = []

    def __init__(self, *args, **kwargs):
        self.columns = kwargs.pop("columns")
        # django metaclass magic to construct fields
        super().__init__(*args, **kwargs)

        self.fields["select_columns"] = forms.MultipleChoiceField(
            choices=self.columns,
            widget=CheckboxSelectMultiple,
            initial=list(self.instance.columns.all().values_list("name", flat=True)),
        )
        # Select(choices=self.columns)

        # Now you can get your choices based on that object id
        # self.fields['my_choice_field'].choices = your_get_choices_function(self.object_id)


class JoinNodeForm(forms.ModelForm):
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


FunctionColumnFormSet = forms.inlineformset_factory(
    Node, FunctionColumn, fields=("name", "function"), extra=1, can_delete=True
)

ColumnFormSet = forms.inlineformset_factory(
    Node, Column, fields=("name",), extra=1, can_delete=True
)


class GroupNodeForm(forms.ModelForm):
    class Meta:
        model = Node
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset("Add columns", Formset("column_form_form_set")),
            Fieldset("Add aggregates", Formset("function_column_form_form_set")),
        )


KIND_TO_FORM = {
    "input": InputNodeForm,
    "select": SelectNodeForm,
    "join": JoinNodeForm,
    "group": GroupNodeForm,
}
KIND_TO_FORMSETS = {"group": [FunctionColumnFormSet, ColumnFormSet]}
