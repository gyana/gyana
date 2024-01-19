from django import forms

from apps.base.formsets import RequiredInlineFormset
from apps.columns.forms import (
    AggregationColumnForm,
    AggregationFormWithFormatting,
    ColumnFormWithFormatting,
)
from apps.columns.models import AggregationColumn, Column
from apps.controls.forms import ControlForm
from apps.controls.models import Control
from apps.filters.forms import FilterForm
from apps.filters.models import Filter

from .models import CombinationChart, Widget

FilterFormset = forms.inlineformset_factory(
    Widget,
    Filter,
    form=FilterForm,
    can_delete=True,
    extra=0,
    formset=RequiredInlineFormset,
)


ColumnFormset = forms.inlineformset_factory(
    Widget,
    Column,
    form=ColumnFormWithFormatting,
    extra=0,
    can_delete=True,
    formset=RequiredInlineFormset,
)


AggregationColumnFormset = forms.inlineformset_factory(
    Widget,
    AggregationColumn,
    form=AggregationColumnForm,
    can_delete=True,
    extra=0,
    formset=RequiredInlineFormset,
)

AggregationWithFormattingFormset = forms.inlineformset_factory(
    Widget,
    AggregationColumn,
    form=AggregationFormWithFormatting,
    can_delete=True,
    extra=0,
    formset=RequiredInlineFormset,
)

ControlFormset = forms.inlineformset_factory(
    Widget,
    Control,
    form=ControlForm,
    can_delete=True,
    max_num=1,
    formset=RequiredInlineFormset,
    extra=0,
)


def create_min_formset(min_num):
    return forms.inlineformset_factory(
        Widget,
        AggregationColumn,
        form=AggregationColumnForm,
        can_delete=True,
        min_num=min_num,
        extra=0,
        formset=RequiredInlineFormset,
    )


SingleMetricFormset = forms.inlineformset_factory(
    Widget,
    AggregationColumn,
    form=AggregationFormWithFormatting,
    can_delete=True,
    extra=0,
    min_num=1,
    max_num=1,
    formset=RequiredInlineFormset,
)

OptionalMetricFormset = forms.inlineformset_factory(
    Widget,
    AggregationColumn,
    form=AggregationColumnForm,
    can_delete=True,
    extra=0,
    max_num=1,
    formset=RequiredInlineFormset,
)


XYMetricFormset = forms.inlineformset_factory(
    Widget,
    AggregationColumn,
    form=AggregationColumnForm,
    # If can_delete is set to true marked as deleted rows are shown again
    can_delete=True,
    extra=0,
    min_num=2,
    max_num=2,
    formset=RequiredInlineFormset,
)

XYZMetricFormset = forms.inlineformset_factory(
    Widget,
    AggregationColumn,
    form=AggregationColumnForm,
    # If can_delete is set to true marked as deleted rows are shown again
    can_delete=True,
    extra=0,
    min_num=3,
    max_num=3,
    formset=RequiredInlineFormset,
)

Min2Formset = create_min_formset(2)
Min3Formset = create_min_formset(3)
# TODO: If at any point these contain more than one value we need to reconsider the logic
# in widgets/widgets.py to calculate the maxMetrics


class CombinationChartForm(AggregationColumnForm):
    class Meta:
        fields = ("kind", "column", "function", "on_secondary")
        model = CombinationChart
        help_texts = {
            "column": "Select the column to aggregate over",
            "function": "Select the aggregation function",
        }
        show = {"function": "column !== null"}
        effect = {
            "column": f"choices.function = $store.ibis.aggregations[schema[column]]",
        }


CombinationChartFormset = forms.inlineformset_factory(
    Widget,
    CombinationChart,
    form=CombinationChartForm,
    can_delete=True,
    min_num=1,
    extra=0,
    formset=RequiredInlineFormset,
)
