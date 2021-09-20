from apps.base.aggregations import AGGREGATION_TYPE_MAP
from apps.base.formsets import RequiredInlineFormset
from apps.base.live_update_form import LiveUpdateForm
from apps.columns.forms import AggregationColumnForm
from apps.columns.models import AggregationColumn
from apps.filters.forms import FilterForm
from apps.filters.models import Filter
from apps.tables.models import Table
from django import forms

from .models import Widget
from .widgets import SourceSelect, VisualSelect


class GenericWidgetForm(LiveUpdateForm):
    dimension = forms.ChoiceField(choices=())
    second_dimension = forms.ChoiceField(choices=())

    class Meta:
        model = Widget
        fields = [
            "table",
            "kind",
            "dimension",
            "second_dimension",
            "sort_by",
            "sort_ascending",
            "stack_100_percent",
        ]
        widgets = {"kind": VisualSelect(), "table": SourceSelect()}

    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660
        project = kwargs.pop("project", None)

        super().__init__(*args, **kwargs)

        if project:
            self.fields["table"].queryset = Table.available.filter(
                project=project
            ).exclude(source="intermediate_node")

    def get_live_fields(self):
        return ["table", "kind"]

    def get_live_formsets(self):
        if self.get_live_field("table") is None:
            return []

        formsets = [FilterFormset]
        kind = self.get_live_field("kind")
        if chart_formsets := FORMSETS.get(kind):
            formsets += chart_formsets
        elif kind not in [Widget.Kind.TABLE]:
            formsets += [AggregationColumnFormset]
        return formsets


class OneDimensionForm(GenericWidgetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        table = self.get_live_field("table")
        schema = Table.objects.get(pk=table).schema if table else None

        if schema and "dimension" in self.fields:
            columns = [
                ("", "No column selected"),
                *[(column, column) for column in schema],
            ]
            self.fields["dimension"].choices = columns

    def get_live_fields(self):
        fields = super().get_live_fields()
        table = self.get_live_field("table")

        if table:
            fields += ["sort_by", "sort_ascending", "dimension"]
        return fields


class TwoDimensionForm(GenericWidgetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        table = self.get_live_field("table")
        schema = Table.objects.get(pk=table).schema if table else None

        if schema:
            columns = [(column, column) for column in schema]
            self.fields["dimension"].choices = columns
            self.fields["dimension"].label = "X"
            self.fields["second_dimension"].choices = columns
            self.fields["second_dimension"].label = "Y"

    def get_live_fields(self):
        fields = super().get_live_fields()
        table = self.get_live_field("table")

        if table:
            fields += ["sort_by", "sort_ascending", "dimension", "second_dimension"]
        return fields


class StackedChartForm(GenericWidgetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        table = self.get_live_field("table")
        schema = Table.objects.get(pk=table).schema if table else None

        if schema:
            choices = [
                ("", "No column selected"),
                *[(column, column) for column in schema],
            ]
            self.fields["dimension"].choices = choices
            self.fields["second_dimension"].choices = choices
            # Can't overwrite label in Meta because we would have to overwrite the whole thing
            self.fields["second_dimension"].label = "Stack dimension"
            self.fields["second_dimension"].required = False

    def get_live_fields(self):
        fields = super().get_live_fields()
        table = self.get_live_field("table")

        if table:
            fields += [
                "sort_by",
                "sort_ascending",
                "dimension",
                "second_dimension",
            ]
            if self.fields["kind"] == Widget.Kind.STACKED_LINE:
                fields += [
                    "stack_100_percent",
                ]
        return fields


FORMS = {
    Widget.Kind.TABLE: GenericWidgetForm,
    Widget.Kind.BAR: OneDimensionForm,
    Widget.Kind.STACKED_COLUMN: StackedChartForm,
    Widget.Kind.COLUMN: OneDimensionForm,
    Widget.Kind.STACKED_BAR: StackedChartForm,
    Widget.Kind.LINE: OneDimensionForm,
    Widget.Kind.STACKED_LINE: StackedChartForm,
    Widget.Kind.PIE: OneDimensionForm,
    Widget.Kind.AREA: OneDimensionForm,
    Widget.Kind.DONUT: OneDimensionForm,
    Widget.Kind.SCATTER: OneDimensionForm,
    Widget.Kind.FUNNEL: GenericWidgetForm,
    Widget.Kind.PYRAMID: GenericWidgetForm,
    Widget.Kind.RADAR: GenericWidgetForm,
    Widget.Kind.HEATMAP: TwoDimensionForm,
    Widget.Kind.BUBBLE: OneDimensionForm,
}


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
    can_delete=False,
    extra=0,
    min_num=2,
    max_num=2,
    formset=RequiredInlineFormset,
)

XYZMetricFormset = forms.inlineformset_factory(
    Widget,
    AggregationColumn,
    form=AggregationColumnForm,
    can_delete=False,
    extra=0,
    min_num=3,
    max_num=3,
    formset=RequiredInlineFormset,
)


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


class WidgetDuplicateForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ()
