# fmt: off
from django import forms

from apps.base.forms import BaseLiveSchemaForm, BaseSchemaForm
from apps.base.formsets import RequiredInlineFormset
from apps.columns.forms import (
    AddColumnForm,
    AggregationColumnForm,
    ColumnForm,
    ConvertColumnForm,
    FormulaColumnForm,
    JoinColumnForm,
    OperationColumnForm,
    WindowColumnForm,
)
from apps.columns.models import (
    AddColumn,
    AggregationColumn,
    Column,
    ConvertColumn,
    EditColumn,
    FormulaColumn,
    JoinColumn,
    RenameColumn,
    SecondaryColumn,
    SortColumn,
    WindowColumn,
)

# fmt: on
from apps.filters.forms import FilterForm
from apps.filters.models import Filter

from .models import Node

AggregationColumnFormSet = forms.inlineformset_factory(
    Node,
    AggregationColumn,
    form=AggregationColumnForm,
    extra=0,
    can_delete=True,
    formset=RequiredInlineFormset,
)


ColumnFormSet = forms.inlineformset_factory(
    Node,
    Column,
    form=ColumnForm,
    extra=0,
    can_delete=True,
    formset=RequiredInlineFormset,
)

SortColumnFormSet = forms.inlineformset_factory(
    Node,
    SortColumn,
    form=BaseLiveSchemaForm,
    fields=("column", "ascending"),
    can_delete=True,
    extra=0,
    min_num=1,
    formset=RequiredInlineFormset,
)


EditColumnFormSet = forms.inlineformset_factory(
    Node,
    EditColumn,
    form=OperationColumnForm,
    can_delete=True,
    extra=0,
    min_num=1,
    formset=RequiredInlineFormset,
)

AddColumnFormSet = forms.inlineformset_factory(
    Node,
    AddColumn,
    form=AddColumnForm,
    can_delete=True,
    extra=0,
    min_num=1,
    formset=RequiredInlineFormset,
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
    form=BaseLiveSchemaForm,
    fields=("column", "new_name"),
    can_delete=True,
    extra=0,
    formset=RequiredInlineFormset,
    min_num=1,
)

FilterFormSet = forms.inlineformset_factory(
    Node, Filter, form=FilterForm, can_delete=True, extra=0, min_num=1
)

SelectColumnFormSet = forms.inlineformset_factory(
    Node,
    SecondaryColumn,
    fields=("column",),
    form=BaseSchemaForm,
    can_delete=True,
    extra=0,
    formset=RequiredInlineFormset,
)

UnpivotColumnFormSet = forms.inlineformset_factory(
    Node,
    Column,
    fields=("column",),
    form=BaseSchemaForm,
    can_delete=True,
    extra=0,
    formset=RequiredInlineFormset,
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

ConvertColumnFormSet = forms.inlineformset_factory(
    Node, ConvertColumn, can_delete=True, form=ConvertColumnForm, extra=0, min_num=1
)

JoinColumnFormset = forms.inlineformset_factory(
    Node,
    JoinColumn,
    form=JoinColumnForm,
    can_delete=True,
    extra=0,
    min_num=1,
    formset=RequiredInlineFormset,
)

KIND_TO_FORMSETS = {
    "aggregation": [ColumnFormSet, AggregationColumnFormSet],
    "sort": [SortColumnFormSet],
    "edit": [EditColumnFormSet],
    "add": [AddColumnFormSet],
    "rename": [RenameColumnFormSet],
    "filter": [FilterFormSet],
    "formula": [FormulaColumnFormSet],
    "unpivot": [UnpivotColumnFormSet, SelectColumnFormSet],
    "window": [WindowColumnFormSet],
    "convert": [ConvertColumnFormSet],
    "join": [JoinColumnFormset],
}
