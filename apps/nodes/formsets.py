# fmt: off
from functools import partial

from django import forms

from apps.base.forms import ModelForm
from apps.base.formsets import BaseInlineFormset, RequiredInlineFormset
from apps.columns.forms import (
    AddColumnForm,
    AggregationColumnForm,
    ColumnForm,
    ConvertColumnForm,
    FormulaColumnForm,
    JoinColumnForm,
    OperationColumnForm,
    RenameColumnForm,
    SortColumnForm,
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

node_formset_factory = partial(
    forms.inlineformset_factory,
    parent_model=Node,
    formset=RequiredInlineFormset,
    can_delete=True,
    extra=0,
)

AggregationColumnFormSet = node_formset_factory(
    model=AggregationColumn, form=AggregationColumnForm
)


ColumnFormSet = node_formset_factory(model=Column, form=ColumnForm)

SortColumnFormSet = node_formset_factory(
    model=SortColumn, form=SortColumnForm, min_num=1
)


EditColumnFormSet = node_formset_factory(
    model=EditColumn, form=OperationColumnForm, min_num=1
)

AddColumnFormSet = node_formset_factory(
    model=AddColumn,
    form=AddColumnForm,
    min_num=1,
)

FormulaColumnFormSet = node_formset_factory(
    model=FormulaColumn, form=FormulaColumnForm, fields=("formula", "label"), min_num=1
)

RenameColumnFormSet = node_formset_factory(
    model=RenameColumn, form=RenameColumnForm, min_num=1
)

FilterFormSet = node_formset_factory(model=Filter, form=FilterForm, min_num=1)

SelectColumnFormSet = node_formset_factory(
    model=SecondaryColumn,
    fields=("column",),
    form=ModelForm,
)

UnpivotColumnFormSet = node_formset_factory(
    model=Column, fields=("column",), form=ModelForm, min_num=1
)

WindowColumnFormSet = forms.inlineformset_factory(
    Node,
    WindowColumn,
    can_delete=True,
    extra=0,
    form=WindowColumnForm,
    min_num=1,
    formset=BaseInlineFormset,
)

ConvertColumnFormSet = forms.inlineformset_factory(
    Node,
    ConvertColumn,
    can_delete=True,
    form=ConvertColumnForm,
    extra=0,
    min_num=1,
    formset=BaseInlineFormset,
)

JoinColumnFormset = node_formset_factory(
    model=JoinColumn, form=JoinColumnForm, min_num=1
)
