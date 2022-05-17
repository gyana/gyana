import copy
import re
import math

from django import forms
from django.db.models import Case, Q, When
from ibis.expr.datatypes import Date, Time, Timestamp

from apps.base.core.utils import create_column_choices
from apps.base.fields import ColorField
from apps.base.forms import (
    BaseModelForm,
    IntegrationSearchMixin,
    LiveFormsetForm,
    LiveFormsetMixin,
)
from apps.base.widgets import Datalist, SelectWithDisable, SourceSelect
from apps.dashboards.forms import PaletteColorsField
from apps.tables.models import Table

from .formsets import FORMSETS, AggregationColumnFormset, ControlFormset, FilterFormset
from .models import COUNT_COLUMN_NAME, WIDGET_KIND_TO_WEB, DEFAULT_WIDTH, DEFAULT_HEIGHT, Widget


def get_not_deleted_entries(data, regex):
    return [
        value
        for key, value in data.items()
        if re.match(re.compile(regex), key) and data.get(key[:-6] + "DELETE") != "on"
    ]


class WidgetCreateForm(BaseModelForm):
    class Meta:
        model = Widget
        fields = ["kind", "x", "y", "page"]

    def __init__(self, *args, **kwargs):
        self.dashboard = kwargs.pop("dashboard", None)
        super().__init__(*args, **kwargs)

    def clean_x(self):
        value = self.cleaned_data["x"]

        # Keep widget within canvas bounds
        value = max(min(value, self.dashboard.width), 0)

        if (value + DEFAULT_WIDTH > self.dashboard.width):
            value = self.dashboard.width - DEFAULT_WIDTH

        if self.dashboard.snap_to_grid:
            value = math.ceil(value / self.dashboard.grid_size) * self.dashboard.grid_size

        return value

    def clean_y(self):
        value = self.cleaned_data["y"]
        
        # Keep widget within canvas bounds
        value = max(min(value, self.dashboard.height), 0)

        if (value + DEFAULT_HEIGHT > self.dashboard.height):
            value = self.dashboard.height - DEFAULT_HEIGHT

        if self.dashboard.snap_to_grid:
            value = math.ceil(value / self.dashboard.grid_size) * self.dashboard.grid_size

        return value


class WidgetSourceForm(IntegrationSearchMixin, BaseModelForm):
    search = forms.CharField(required=False)

    class Meta:
        model = Widget
        fields = ["table"]
        widgets = {"table": SourceSelect(parent="dashboard")}

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)

        super().__init__(*args, **kwargs)
        self.order_fields(["search", "table"])
        self.fields["search"].widget.attrs["data-action"] = "input->tf-modal#search"

        # Re-focus the search bar when there is a value
        if self.data.get("search"):
            self.fields["search"].widget.attrs["autofocus"] = ""

        if project:
            self.search_queryset(
                self.fields["table"],
                project,
                self.instance.table,
                self.instance.page.dashboard.input_tables_fk,
            )


class GenericWidgetForm(LiveFormsetForm):
    dimension = forms.ChoiceField(choices=())
    second_dimension = forms.ChoiceField(choices=())
    sort_column = forms.ChoiceField(choices=(), required=False)

    class Meta:
        model = Widget
        fields = [
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["kind"].choices = [
            choice
            for choice in self.fields["kind"].choices
            if choice[0]
            not in [Widget.Kind.TEXT, Widget.Kind.IMAGE, Widget.Kind.IFRAME]
        ]

        schema = self.instance.table.schema
        if "date_column" in self.fields:
            self.fields["date_column"] = forms.ChoiceField(
                required=False,
                widget=SelectWithDisable(
                    disabled=disable_non_time(schema),
                ),
                choices=create_column_choices(schema),
                help_text=self.base_fields["date_column"].help_text,
            )

        if self.get_live_field("kind") == Widget.Kind.TABLE:
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
            if columns := group_columns + aggregations:
                if not aggregations:
                    columns += [COUNT_COLUMN_NAME]
                self.fields["sort_column"].choices = [("", "No column selected")] + [
                    (name, name) for name in columns
                ]
            else:
                self.fields["sort_column"].choices = create_column_choices(schema)

    def get_live_fields(self):
        fields = ["kind", "date_column"]

        if self.get_live_field("kind") == Widget.Kind.TABLE:
            fields += ["sort_column", "sort_ascending", "show_summary_row"]

        if (
            self.get_live_field("kind") == Widget.Kind.METRIC
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

        schema = self.instance.table.schema

        if "dimension" in self.fields:

            if is_timeseries_chart(self.get_live_field("kind")):
                self.fields["dimension"].widget = SelectWithDisable(
                    disabled=disable_non_time(schema)
                )
            self.fields["dimension"].choices = create_column_choices(schema)

    def get_live_fields(self):
        fields = super().get_live_fields()
        fields += ["dimension"]
        if self.get_live_field("kind") != Widget.Kind.COMBO:
            fields += ["sort_by", "sort_ascending"]

        schema = self.instance.table.schema

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

        schema = self.instance.table.schema

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
        fields += ["dimension", "second_dimension"]

        schema = self.instance.table.schema

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

        schema = self.instance.table.schema

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

        fields += [
            "dimension",
            "second_dimension",
        ]
        if self.get_live_field("kind") != Widget.Kind.STACKED_LINE:
            fields += [
                "stack_100_percent",
            ]

        schema = self.instance.table.schema

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
    Widget.Kind.GAUGE: GenericWidgetForm,
}


class WidgetDuplicateForm(BaseModelForm):
    class Meta:
        model = Widget
        fields = ()


class StyleMixin:
    def get_initial_for_field(self, field, field_name):
        if self.initial.get(field_name) != None and getattr(self.instance, field_name):
            return self.initial.get(field_name)

        # Field has no value but dashboard has set a value.
        if hasattr(self.instance.page.dashboard, f"widget_{field_name}"):
            return getattr(self.instance.page.dashboard, f"widget_{field_name}")

        if hasattr(self.instance.page.dashboard, field_name):
            return getattr(self.instance.page.dashboard, field_name)

        if field.initial:
            return field.initial

        return super().get_initial_for_field(field, field_name)


class DefaultStyleForm(StyleMixin, BaseModelForm):
    palette_colors = PaletteColorsField(required=False)
    background_color = ColorField(required=False, initial="#ffffff")

    class Meta:
        model = Widget
        fields = [
            "palette_colors",
            "background_color",
            "show_tooltips",
            "font_size",
            "currency",
        ]
        widgets = {
            "currency": Datalist(attrs={"data-live-update-ignore": ""}),
        }


class TableStyleForm(StyleMixin, BaseModelForm):
    background_color = ColorField(required=False, initial="#ffffff")

    class Meta:
        model = Widget
        fields = [
            "table_show_header",
            "table_hide_data_type",
            "table_paginate_by",
            "background_color",
        ]


class MetricStyleForm(StyleMixin, BaseModelForm):
    background_color = ColorField(required=False, initial="#ffffff")

    metric_header_font_size = forms.IntegerField(
        required=False,
        initial=16,
        widget=forms.NumberInput(
            attrs={"class": "label--half", "unit_suffix": "pixels"}
        ),
    )
    metric_header_font_color = forms.CharField(
        required=False,
        initial="#6a6b77",
        widget=forms.TextInput(attrs={"class": "label--half", "type": "color"}),
    )
    metric_font_size = forms.IntegerField(
        required=False,
        initial=60,
        widget=forms.NumberInput(
            attrs={"class": "label--half", "unit_suffix": "pixels"}
        ),
    )
    metric_font_color = forms.CharField(
        required=False,
        initial="#242733",
        widget=forms.TextInput(attrs={"class": "label--half", "type": "color"}),
    )
    metric_comparison_font_size = forms.IntegerField(
        required=False,
        initial=30,
        widget=forms.NumberInput(
            attrs={"class": "label--half", "unit_suffix": "pixels"}
        ),
    )
    metric_comparison_font_color = forms.CharField(
        required=False,
        initial="#6a6b77",
        widget=forms.TextInput(attrs={"class": "label--half", "type": "color"}),
    )

    class Meta:
        model = Widget
        fields = [
            "background_color",
            "metric_header_font_size",
            "metric_header_font_color",
            "metric_font_size",
            "metric_font_color",
            "metric_comparison_font_size",
            "metric_comparison_font_color",
        ]


class GaugeStyleForm(StyleMixin, BaseModelForm):
    background_color = ColorField(required=False, initial="#ffffff")
    first_segment_color = ColorField(required=False, initial="#e30303")
    second_segment_color = ColorField(required=False, initial="#f38e4f")
    third_segment_color = ColorField(required=False, initial="#facc15")
    fourth_segment_color = ColorField(required=False, initial="#0db145")

    class Meta:
        model = Widget
        fields = [
            "background_color",
            "lower_limit",
            "upper_limit",
            "show_tooltips",
            "currency",
            "first_segment_color",
            "second_segment_color",
            "third_segment_color",
            "fourth_segment_color",
        ]


STYLE_FORMS = {
    Widget.Kind.METRIC: MetricStyleForm,
    Widget.Kind.TABLE: TableStyleForm,
    Widget.Kind.GAUGE: GaugeStyleForm,
}
