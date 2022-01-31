import copy
import re

from django import forms
from ibis.expr.datatypes import Date, Time, Timestamp

from apps.base.core.utils import create_column_choices
from apps.base.forms import BaseModelForm, LiveFormsetForm, LiveFormsetMixin
from apps.base.widgets import SelectWithDisable
from apps.dashboards.forms import PaletteColorsField
from apps.tables.models import Table

from .formsets import FORMSETS, AggregationColumnFormset, ControlFormset, FilterFormset
from .models import COUNT_COLUMN_NAME, WIDGET_KIND_TO_WEB, Widget
from .widgets import SourceSelect


def get_not_deleted_entries(data, regex):
    return [
        value
        for key, value in data.items()
        if re.match(re.compile(regex), key) and data.get(key[:-6] + "DELETE") != "on"
    ]


class GenericWidgetForm(LiveFormsetForm):
    dimension = forms.ChoiceField(choices=())
    second_dimension = forms.ChoiceField(choices=())
    sort_column = forms.ChoiceField(choices=(), required=False)

    class Meta:
        model = Widget
        fields = [
            "table",
            "kind",
            "dimension",
            "part",
            "second_dimension",
            "sort_by",
            "sort_column",
            "sort_ascending",
            "stack_100_percent",
            "date_column",
            "show_summary_row",
            "compare_previous_period",
            "positive_decrease",
        ]
        widgets = {"table": SourceSelect()}

    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660
        project = kwargs.pop("project", None)

        super().__init__(*args, **kwargs)
        self.fields["kind"].choices = [
            choice
            for choice in self.fields["kind"].choices
            if choice[0]
            not in [Widget.Kind.TEXT, Widget.Kind.IMAGE, Widget.Kind.IFRAME]
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

            if table and self.get_live_field("kind") == Widget.Kind.TABLE:
                formsets = self.get_formsets()
                group_columns = [
                    form.data[f"{form.prefix}-column"]
                    for form in formsets["Group columns"].forms
                    if not form.deleted and form.data.get(f"{form.prefix}-column")
                ]
                aggregations = [
                    form.data[f"{form.prefix}-column"]
                    for form in formsets["Aggregations"].forms
                    if not form.deleted and form.data.get(f"{form.prefix}-column")
                ]
                columns = group_columns + aggregations
                if columns:
                    if not aggregations:
                        columns += [COUNT_COLUMN_NAME]
                    self.fields["sort_column"].choices = [
                        ("", "No column selected")
                    ] + [(name, name) for name in columns]
                else:
                    self.fields["sort_column"].choices = create_column_choices(schema)

    def get_live_fields(self):
        fields = ["table", "kind"]
        table = self.get_live_field("table")
        if table:
            fields += ["date_column"]

        if self.get_live_field("kind") == Widget.Kind.TABLE and table:
            fields += ["sort_column", "sort_ascending", "show_summary_row"]

        if (
            self.get_live_field("kind") == Widget.Kind.METRIC
            and table
            and self.get_live_field("date_column")
            and (
                self.instance.page.has_control
                or (
                    (controls := self.get_formsets().get("control"))
                    and len([form for form in controls.forms if not form.deleted]) == 1
                )
            )
        ):
            fields += ["compare_previous_period", "positive_decrease"]
        return fields

    def get_live_formsets(self):
        if self.get_live_field("table") is None:
            return []

        formsets = [FilterFormset]

        if self.get_live_field("date_column"):
            # Inserting at the beginning because we want it to be before the filter
            formsets.insert(0, ControlFormset)
        kind = self.get_live_field("kind")
        if chart_formsets := FORMSETS.get(kind):
            formsets += chart_formsets
        else:
            formsets += [AggregationColumnFormset]

        return formsets

    def get_formset_kwargs(self, formset):
        kind = self.get_live_field("kind")
        if kind == Widget.Kind.SCATTER:
            return {"names": ["X", "Y"]}
        if kind == Widget.Kind.BUBBLE:
            return {"names": ["X", "Y", "Z"]}
        return {}


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
            schema = (
                Table.objects.get(pk=table).schema
                if isinstance(table, (str, int))
                else table.schema
            )

            if (
                (dimension := self.get_live_field("dimension"))
                and dimension in schema
                and isinstance(schema[dimension], (Date, Timestamp))
            ):
                fields += ["part"]
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

            schema = (
                Table.objects.get(pk=table).schema
                if isinstance(table, (str, int))
                else table.schema
            )

            if (
                (dimension := self.get_live_field("dimension"))
                and dimension in schema
                and isinstance(schema[dimension], (Date, Timestamp))
            ):
                fields += ["part"]
        return fields


class StackedChartForm(GenericWidgetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        table = self.get_live_field("table")
        schema = Table.objects.get(pk=table).schema if table else None

        if schema:
            choices = create_column_choices(schema)
            if is_timeseries_chart(self.get_live_field("kind")):
                self.fields["dimension"].widget = SelectWithDisable(
                    disabled=disable_non_time(schema)
                )
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

            schema = (
                Table.objects.get(pk=table).schema
                if isinstance(table, (str, int))
                else table.schema
            )

            if (
                (dimension := self.get_live_field("dimension"))
                and dimension in schema
                and isinstance(schema[dimension], (Date, Timestamp))
            ):
                fields += ["part"]

        return fields


class IframeWidgetForm(LiveFormsetMixin, BaseModelForm):
    url = forms.URLField(
        label="Embed URL",
        widget=forms.URLInput(
            attrs={"placeholder": "e.g. https://markets.ft.com/data/"}
        ),
        required=False,
    )

    class Meta:
        model = Widget
        fields = [
            "url",
        ]

    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660
        project = kwargs.pop("project", None)

        super().__init__(*args, **kwargs)


class ImageWidgetForm(LiveFormsetMixin, BaseModelForm):
    class Meta:
        model = Widget
        fields = [
            "kind",
            "image",
        ]
        widgets = {"kind": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660
        project = kwargs.pop("project", None)

        super().__init__(*args, **kwargs)


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
    Widget.Kind.IFRAME: IframeWidgetForm,
    Widget.Kind.IMAGE: ImageWidgetForm,
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
