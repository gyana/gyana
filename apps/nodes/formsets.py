# fmt: off
from apps.base.formsets import InlineColumnFormset
from apps.base.live_update_form import LiveUpdateForm
from apps.base.schema_form_mixin import SchemaFormMixin
from apps.columns.forms import (AddColumnForm, FormulaColumnForm,
                                AggreggationColumnForm, OperationColumnForm,
                                WindowColumnForm)
from apps.columns.models import (AddColumn, Column, EditColumn, FormulaColumn,
                                 AggreggationColumn, RenameColumn, SecondaryColumn,
                                 SortColumn, WindowColumn)
# fmt: on
from apps.filters.forms import FilterForm
from apps.filters.models import Filter
from django import forms

from .models import Node

AggreggationColumnFormSet = forms.inlineformset_factory(
    Node,
    AggreggationColumn,
    form=AggreggationColumnForm,
    extra=0,
    can_delete=True,
    formset=InlineColumnFormset,
)

ColumnFormSet = forms.inlineformset_factory(
    Node,
    Column,
    form=LiveUpdateForm,
    fields=("column",),
    extra=0,
    can_delete=True,
    formset=InlineColumnFormset,
)


SortColumnFormSet = forms.inlineformset_factory(
    Node,
    SortColumn,
    form=LiveUpdateForm,
    fields=("column", "ascending"),
    can_delete=True,
    extra=0,
    min_num=1,
    formset=InlineColumnFormset,
)


EditColumnFormSet = forms.inlineformset_factory(
    Node,
    EditColumn,
    form=OperationColumnForm,
    can_delete=True,
    extra=0,
    min_num=1,
    formset=InlineColumnFormset,
)

AddColumnFormSet = forms.inlineformset_factory(
    Node,
    AddColumn,
    form=AddColumnForm,
    can_delete=True,
    extra=0,
    min_num=1,
    formset=InlineColumnFormset,
)

FormulaColumnFormSet = forms.inlineformset_factory(
    Node,
    FormulaColumn,
    form=FormulaColumnForm,
    fields=("formula", "label"),
    can_delete=True,
    extra=0,
    min_num=1,
)

RenameColumnFormSet = forms.inlineformset_factory(
    Node,
    RenameColumn,
    form=type(
        "RenameColumnForm",
        (
            SchemaFormMixin,
            LiveUpdateForm,
        ),
        {},
    ),
    fields=("column", "new_name"),
    can_delete=True,
    extra=0,
    formset=InlineColumnFormset,
    min_num=1,
)

FilterFormSet = forms.inlineformset_factory(
    Node, Filter, form=FilterForm, can_delete=True, extra=0, min_num=1
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
    min_num=1,
)

WindowColumnFormSet = forms.inlineformset_factory(
    Node,
    WindowColumn,
    can_delete=True,
    extra=0,
    form=WindowColumnForm,
    min_num=1,
)

KIND_TO_FORMSETS = {
    "aggregation": [AggreggationColumnFormSet, ColumnFormSet],
    "sort": [SortColumnFormSet],
    "edit": [EditColumnFormSet],
    "add": [AddColumnFormSet],
    "rename": [RenameColumnFormSet],
    "filter": [FilterFormSet],
    "formula": [FormulaColumnFormSet],
    "unpivot": [UnpivotColumnFormSet, SelectColumnFormSet],
    "window": [WindowColumnFormSet],
}
