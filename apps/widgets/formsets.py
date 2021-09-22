from apps.base.formsets import RequiredInlineFormset
from apps.columns.forms import AggregationColumnForm
from apps.columns.models import AggregationColumn
from apps.filters.forms import FilterForm
from apps.filters.models import Filter
from django import forms

from .models import Widget

FilterFormset = forms.inlineformset_factory(
    Widget,
    Filter,
    form=FilterForm,
    can_delete=True,
    extra=0,
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


# TODO: If at any point these contain more than one value we need to reconsider the logic
# in widgets/widgets.py to calculate the maxMetrics
FORMSETS = {
    Widget.Kind.PIE: [SingleMetricFormset],
    Widget.Kind.STACKED_BAR: [SingleMetricFormset],
    Widget.Kind.STACKED_COLUMN: [SingleMetricFormset],
    Widget.Kind.SCATTER: [XYMetricFormset],
    Widget.Kind.BUBBLE: [XYZMetricFormset],
    Widget.Kind.HEATMAP: [SingleMetricFormset],
    Widget.Kind.RADAR: [create_min_formset(3)],
    Widget.Kind.PYRAMID: [create_min_formset(2)],
    Widget.Kind.FUNNEL: [create_min_formset(2)],
}
