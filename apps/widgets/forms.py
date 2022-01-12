import copy

from django import forms
from ibis.expr.datatypes import Date, Time, Timestamp

from apps.base.live_update_form import LiveUpdateForm
from apps.base.utils import create_column_choices
from apps.base.widgets import SelectWithDisable
from apps.dashboards.forms import PaletteColorsField
from apps.tables.models import Table

from .formsets import FORMSETS, AggregationColumnFormset, FilterFormset
from .models import WIDGET_KIND_TO_WEB, Widget
from .widgets import SourceSelect


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
            "date_column",
            "show_summary_row",
        ]
        widgets = {"table": SourceSelect()}

    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660
        project = kwargs.pop("project", None)

        super().__init__(*args, **kwargs)
        self.fields["kind"].choices = [
            choice
            for choice in self.fields["kind"].choices
            if choice[0] != Widget.Kind.TEXT
        ]
        if project:
            self.fields["table"].queryset = Table.available.filter(
                project=project
            ).exclude(
                source__in=[Table.Source.INTERMEDIATE_NODE, Table.Source.CACHE_NODE]
            )
            table = self.get_live_field("table")
            schema = Table.objects.get(pk=table).schema if table else None
            if "date_column" in self.fields and schema:
                self.fields["date_column"] = forms.ChoiceField(
                    required=False,
                    widget=SelectWithDisable(
                        disabled=disable_non_time(schema),
                    ),
                    choices=create_column_choices(schema),
                    help_text=self.base_fields["date_column"].help_text,
                )

    def get_live_fields(self):
        fields = ["table", "kind"]

        if self.get_live_field("table") and self.instance.page.has_control:
            fields += ["date_column"]

        if self.get_live_field("kind") == Widget.Kind.TABLE and self.get_live_field(
            "table"
        ):
            fields += ["show_summary_row"]
        return fields

    def get_live_formsets(self):
        if self.get_live_field("table") is None:
            return []

        formsets = [FilterFormset]
        kind = self.get_live_field("kind")
        if chart_formsets := FORMSETS.get(kind):
            formsets += chart_formsets
        else:
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
            fields += ["dimension"]
            if self.get_live_field("kind") != Widget.Kind.COMBO:
                fields += ["sort_by", "sort_ascending"]
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
            fields += ["dimension", "second_dimension"]
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
    Widget.Kind.COMBO: OneDimensionForm,
}


class WidgetDuplicateForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ()


class WidgetStyleForm(forms.ModelForm):
    palette_colors = PaletteColorsField(required=False)
    background_color = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"type": "color"}),
    )

    class Meta:
        model = Widget
        fields = [
            "palette_colors",
            "background_color",
            "show_tooltips",
            "font_size",
            "rounding_decimal",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.kind == Widget.Kind.METRIC:
            self.fields = copy.deepcopy(
                {
                    key: field
                    for key, field in self.base_fields.items()
                    if key not in ["palette_color", "font_size", "show_tooltips"]
                }
            )
        else:
            self.fields = {
                key: field
                for key, field in self.base_fields.items()
                if key != "rounding_decimal"
            }

    # If widget has no value set for a setting, default to dashboard settings.
    def get_initial_for_field(self, field, field_name):
        if getattr(self.instance, field_name) is not None:
            return super().get_initial_for_field(field, field_name)

        if hasattr(self.instance.page.dashboard, field_name):
            return getattr(self.instance.page.dashboard, field_name)

        return super().get_initial_for_field(field, field_name)
