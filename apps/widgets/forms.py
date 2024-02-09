import math

from crispy_forms.layout import Layout
from django import forms
from ibis.expr.datatypes import Date, Time, Timestamp

from apps.base.crispy import CrispyFormset
from apps.base.fields import ColorField
from apps.base.forms import ModelForm
from apps.base.widgets import Datalist
from apps.columns.fields import ColumnField
from apps.dashboards.widgets import PaletteColorsField
from apps.tables.widgets import TableSelect

from .formsets import (
    AggregationColumnFormset,
    AggregationWithFormattingFormset,
    ColumnFormset,
    CombinationChartFormset,
    ControlFormset,
    FilterFormset,
    Min2Formset,
    Min3Formset,
    OptionalMetricFormset,
    SingleMetricFormset,
    XYMetricFormset,
    XYZMetricFormset,
)
from .models import CATEGORIES, DEFAULT_HEIGHT, DEFAULT_WIDTH, Widget


class WidgetCreateForm(ModelForm):
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

        if value + DEFAULT_WIDTH > self.dashboard.width:
            value = self.dashboard.width - DEFAULT_WIDTH

        if self.dashboard.snap_to_grid:
            value = (
                math.ceil(value / self.dashboard.grid_size) * self.dashboard.grid_size
            )

        return value

    def clean_y(self):
        value = self.cleaned_data["y"]

        # Keep widget within canvas bounds
        value = max(min(value, self.dashboard.height), 0)

        if value + DEFAULT_HEIGHT > self.dashboard.height:
            value = self.dashboard.height - DEFAULT_HEIGHT

        if self.dashboard.snap_to_grid:
            value = (
                math.ceil(value / self.dashboard.grid_size) * self.dashboard.grid_size
            )

        return value


class WidgetSourceForm(ModelForm):
    class Meta:
        model = Widget
        fields = ["table"]
        widgets = {"table": TableSelect(parent="dashboard")}

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        self.fields["table"].widget.parent_entity = self.instance.page.dashboard


class GenericWidgetForm(ModelForm):
    dimension = forms.ChoiceField(choices=())
    second_dimension = forms.ChoiceField(choices=())
    sort_column = forms.ChoiceField(choices=(), required=False)
    dimension = ColumnField()
    second_dimension = ColumnField()
    sort_column = ColumnField(required=False)
    date_column = ColumnField(
        required=False,
        allowed_types=(Date, Time, Timestamp),
        message="You can only select datetime, time or date columns for timeseries charts.",
    )

    class Meta:
        model = Widget
        fields = [
            "kind",
            "dimension",
            "part",
            "second_dimension",
            "sort_column",
            "sort_ascending",
            "stack_100_percent",
            "date_column",
            "show_summary_row",
            "compare_previous_period",
            "positive_decrease",
        ]
        formsets = {
            "default_metrics": AggregationColumnFormset,
            "optional_metrics": OptionalMetricFormset,
            "xy": XYMetricFormset,
            "xyz": XYZMetricFormset,
            "min3": Min3Formset,
            "min2": Min2Formset,
            "single_metric": SingleMetricFormset,
            "combo": CombinationChartFormset,
            "dimensions": ColumnFormset,
            "metrics": AggregationWithFormattingFormset,
            "controls": ControlFormset,
            "filters": FilterFormset,
        }

        K = Widget.Kind

        def is_kind(*args):
            if len(args) == 1:
                return f"kind === '{args[0]}'"
            return f"{[str(k) for k in args]}.includes(kind)"

        def is_not_kind(*args):
            if len(args) == 1:
                return f"kind !== '{args[0]}'"
            return f"!{[str(k) for k in args]}.includes(kind)"

        show = {
            "dimension": is_not_kind(K.METRIC, K.TABLE, K.COMBO),
            # TODO: custom form for datetime parts, possibly with a multi-widget
            "part": "dimension !== null && ['Date', 'Timestamp'].includes(schema[dimension])",
            "second_dimension": is_kind(
                K.STACKED_COLUMN, K.STACKED_BAR, K.STACKED_LINE, K.HEATMAP
            ),
            "sort_column": is_not_kind(K.METRIC, K.COMBO, K.HEATMAP),
            "sort_ascending": is_not_kind(K.METRIC, K.COMBO, K.HEATMAP),
            "stack_100_percent": is_kind(
                K.STACKED_COLUMN, K.STACKED_BAR, K.STACKED_LINE
            ),
            "show_summary_row": is_kind(K.TABLE),
            # TODO: need to check for existence of control on page OR add a note to say this is required
            "compare_previous_period": f"kind === '{K.METRIC}' && date_column !== null",
            "positive_decrease": f"kind === '{K.METRIC}' && date_column !== null",
            # formsets
            "default_metrics": is_kind(K.COLUMN, K.BAR, K.LINE, K.AREA, K.DONUT),
            "optional_metrics": is_kind(
                K.PIE, K.STACKED_BAR, K.STACKED_COLUMN, K.STACKED_LINE, K.HEATMAP
            ),
            "xy": is_kind(K.SCATTER),
            "xyz": is_kind(K.BUBBLE),
            "min3": is_kind(K.RADAR),
            "min2": is_kind(K.FUNNEL),
            "single_metric": is_kind(K.METRIC, K.GAUGE),
            "combo": is_kind(K.COMBO),
            "dimensions": is_kind(K.TABLE),
            "metrics": is_kind(K.TABLE),
            "controls": "date_column !== null",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["kind"].choices = [
            (key.label, values)
            for key, values in CATEGORIES.items()
            if key != Widget.Category.CONTENT
        ]

        # TODO: implement sort as a formset of WidgetSortColumn (new model)
        # generated name is implementation detail for BigQuery
        # write a migration for existing column name
        # include COUNT_COLUMN_NAME as a default option
        # if "sort_column" in self.fields:
        #     self.fields["sort_column"].choices = choices

        # TODO with Alpine for heatmap
        # self.fields["dimension"].label = "X"
        # self.fields["second_dimension"].label = "Y"

        # TODO with Alpine for stacked chart
        # self.fields["second_dimension"].label = "Stack dimension"
        # self.fields["second_dimension"].required = False

        self.helper.layout = Layout(
            "kind",
            "dimension",
            "part",
            "second_dimension",
            CrispyFormset("default_metrics", "Metrics"),
            CrispyFormset("optional_metrics", "Optional metrics"),
            CrispyFormset("xy", "Metrics"),
            CrispyFormset("xyz", "Metrics"),
            CrispyFormset("min3", "Metrics (minimum 3)"),
            CrispyFormset("min2", "Metrics (minimum 2)"),
            CrispyFormset("single_metric", "Metric"),
            CrispyFormset("combo", "Metrics"),
            CrispyFormset("dimensions", "Dimensions"),
            CrispyFormset("metrics", "Metrics"),
            "sort_column",
            "sort_ascending",
            "stack_100_percent",
            "date_column",
            "show_summary_row",
            "compare_previous_period",
            "positive_decrease",
            CrispyFormset("controls", "Controls"),
            CrispyFormset("filters", "Filters"),
        )

    def get_formset_kwargs(self, formset):
        if formset == XYMetricFormset:
            return {"names": ["X", "Y"]}
        if formset == XYZMetricFormset:
            return {"names": ["X", "Y", "Z"]}
        return {}


class TextWidgetForm(ModelForm):
    class Meta:
        model = Widget
        fields = ["text_content"]
        widgets = {"text_content": forms.HiddenInput(attrs={"x-model": "text"})}

    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660
        project = kwargs.pop("project", None)

        super().__init__(*args, **kwargs)


class IframeWidgetForm(ModelForm):
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


class ImageWidgetForm(ModelForm):
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
    Widget.Kind.IFRAME: IframeWidgetForm,
    Widget.Kind.IMAGE: ImageWidgetForm,
    Widget.Kind.GAUGE: GenericWidgetForm,
}


class WidgetDuplicateForm(ModelForm):
    class Meta:
        model = Widget
        fields = ()


class StyleMixin:
    def get_initial_for_field(self, field, field_name):
        if self.initial.get(field_name) != None and hasattr(self.instance, field_name):
            return self.initial.get(field_name)

        # Field has no value but dashboard has set a value.
        if hasattr(self.instance.page.dashboard, f"widget_{field_name}"):
            return getattr(self.instance.page.dashboard, f"widget_{field_name}")

        if hasattr(self.instance.page.dashboard, field_name):
            return getattr(self.instance.page.dashboard, field_name)

        if field.initial:
            return field.initial

        return super().get_initial_for_field(field, field_name)


class DefaultStyleForm(StyleMixin, ModelForm):
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
            "currency": Datalist(),
        }

    ignore_live_update_fields = ["currency"]


class TableStyleForm(StyleMixin, ModelForm):
    background_color = ColorField(required=False, initial="#ffffff")

    class Meta:
        model = Widget
        fields = [
            "table_show_header",
            "table_hide_data_type",
            "table_paginate_by",
            "background_color",
        ]


class MetricStyleForm(StyleMixin, ModelForm):
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


class GaugeStyleForm(StyleMixin, ModelForm):
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
