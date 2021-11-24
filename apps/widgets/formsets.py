from django import forms

from apps.base.formsets import RequiredInlineFormset
from apps.columns.forms import AggregationColumnForm
from apps.columns.models import AggregationColumn
from apps.filters.forms import FilterForm
from apps.filters.models import Filter

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
FORMSETS = {
    Widget.Kind.PIE: [OptionalMetricFormset],
    Widget.Kind.STACKED_BAR: [OptionalMetricFormset],
    Widget.Kind.STACKED_COLUMN: [OptionalMetricFormset],
    Widget.Kind.SCATTER: [XYMetricFormset],
    Widget.Kind.BUBBLE: [XYZMetricFormset],
    Widget.Kind.HEATMAP: [OptionalMetricFormset],
    Widget.Kind.RADAR: [Min3Formset],
    Widget.Kind.PYRAMID: [Min2Formset],
    Widget.Kind.FUNNEL: [Min2Formset],
    Widget.Kind.METRIC: [SingleMetricFormset],
}
