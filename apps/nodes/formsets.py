# fmt: off
from apps.columns.forms import (AddColumnForm, FormulaColumnForm,
                                FunctionColumnForm, OperationColumnForm,
                                WindowColumnForm)
# fmt: on
from apps.filters.forms import FilterForm
from apps.filters.models import Filter
from django import forms
from django.forms.models import BaseInlineFormSet

# fmt: off
from .models import (AddColumn, Column, EditColumn, FormulaColumn,
                     FunctionColumn, Node, RenameColumn, SecondaryColumn,
                     SortColumn, WindowColumn)

# fmt: on


class InlineColumnFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.form.base_fields["column"] = forms.ChoiceField(
            choices=[
                ("", "No column selected"),
                *[(col, col) for col in self.instance.parents.first().schema],
            ]
        )


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


EditColumnFormSet = forms.inlineformset_factory(
    Node,
    EditColumn,
    form=OperationColumnForm,
    can_delete=True,
    extra=0,
    formset=InlineColumnFormset,
)

AddColumnFormSet = forms.inlineformset_factory(
    Node,
    AddColumn,
    form=AddColumnForm,
    can_delete=True,
    extra=0,
    formset=InlineColumnFormset,
)

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

WindowColumnFormSet = forms.inlineformset_factory(
    Node, WindowColumn, can_delete=True, extra=True, form=WindowColumnForm
)

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
