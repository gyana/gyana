from apps.base.live_update_form import LiveUpdateForm
from apps.tables.models import Table
from django import forms

from .formsets import FORMSETS, AggregationColumnFormset, FilterFormset
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
