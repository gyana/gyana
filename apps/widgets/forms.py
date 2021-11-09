from django import forms
from ibis.expr.datatypes import Date, Time, Timestamp

from apps.base.live_update_form import LiveUpdateForm
from apps.base.utils import create_column_choices
from apps.base.widgets import SelectWithDisable
from apps.tables.models import Table

from .formsets import FORMSETS, AggregationColumnFormset, FilterFormset
from .models import WIDGET_KIND_TO_WEB, Widget
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
            ).exclude(
                source__in=[Table.Source.INTERMEDIATE_NODE, Table.Source.CACHE_NODE]
            )

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


def disable_non_time(schema):
    return {
        name: "You can only select datetime, time or date columns for timeseries charts."
        for name, type_ in schema.items()
        if not isinstance(type_, (Time, Timestamp, Date))
    }


def is_timeseries_chart(kind):
    return WIDGET_KIND_TO_WEB[kind][1] == Widget.Category.TIMESERIES


class OneDimensionForm(GenericWidgetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        table = self.get_live_field("table")
        schema = Table.objects.get(pk=table).schema if table else None

        if schema and "dimension" in self.fields:

            if is_timeseries_chart(self.get_live_field("kind")):
                self.fields["dimension"].widget = SelectWithDisable(
                    disabled=disable_non_time(schema)
                )
            self.fields["dimension"].choices = create_column_choices(schema)

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
            columns = create_column_choices(schema)
            if is_timeseries_chart(self.get_live_field("kind")):
                self.fields["dimension"].widget = SelectWithDisable(
                    disabled=disable_non_time(schema)
                )
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
            choices = create_column_choices(schema)

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
            if self.get_live_field("kind") != Widget.Kind.STACKED_LINE:
                fields += [
                    "stack_100_percent",
                ]
        return fields


FORMS = {
    Widget.Kind.TABLE: GenericWidgetForm,
    Widget.Kind.BAR: OneDimensionForm,
    Widget.Kind.STACKED_COLUMN: StackedChartForm,
    Widget.Kind.COLUMN: OneDimensionForm,
    Widget.Kind.TIMESERIES_STACKED_COLUMN: StackedChartForm,
    Widget.Kind.TIMESERIES_COLUMN: OneDimensionForm,
    Widget.Kind.STACKED_BAR: StackedChartForm,
    Widget.Kind.LINE: OneDimensionForm,
    Widget.Kind.TIMESERIES_STACKED_LINE: StackedChartForm,
    Widget.Kind.TIMESERIES_LINE: OneDimensionForm,
    Widget.Kind.STACKED_LINE: StackedChartForm,
    Widget.Kind.PIE: OneDimensionForm,
    Widget.Kind.AREA: OneDimensionForm,
    Widget.Kind.TIMESERIES_AREA: OneDimensionForm,
    Widget.Kind.DONUT: OneDimensionForm,
    Widget.Kind.SCATTER: OneDimensionForm,
    Widget.Kind.FUNNEL: GenericWidgetForm,
    Widget.Kind.PYRAMID: GenericWidgetForm,
    Widget.Kind.RADAR: GenericWidgetForm,
    Widget.Kind.HEATMAP: TwoDimensionForm,
    Widget.Kind.BUBBLE: OneDimensionForm,
    Widget.Kind.METRIC: GenericWidgetForm,
}


class WidgetDuplicateForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ()
