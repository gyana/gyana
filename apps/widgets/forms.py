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
    label = forms.ChoiceField(choices=())
    value = forms.ChoiceField(choices=())
    z = forms.ChoiceField(choices=())

    class Meta:
        model = Widget
        fields = [
            "table",
            "kind",
            "label",
            "z",
            "z_aggregator",
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
        if self.instance.kind in [
            Widget.Kind.PIE,
            Widget.Kind.STACKED_BAR,
            Widget.Kind.STACKED_COLUMN,
        ]:
            formsets += [SingleValueFormset]
        elif self.instance.kind not in [Widget.Kind.TABLE]:
            formsets += [AggregationColumnFormset]
        return formsets


class TwoDimensionForm(GenericWidgetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        table = self.get_live_field("table")
        schema = Table.objects.get(pk=table).schema if table else None

        if schema and "label" in self.fields:
            columns = [
                ("", "No column selected"),
                *[(column, column) for column in schema],
            ]
            self.fields["label"].choices = columns

    def get_live_fields(self):
        fields = super().get_live_fields()
        table = self.get_live_field("table")

        if table:
            fields += ["sort_by", "sort_ascending", "label"]
        return fields


class ThreeDimensionForm(GenericWidgetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        table = self.get_live_field("table")
        schema = Table.objects.get(pk=table).schema if table else None

        if schema:
            columns = [(column, column) for column in schema]
            self.fields["label"].choices = columns
            self.fields["z"].choices = columns

            kind = self.get_live_field("kind")
            if kind in [Widget.Kind.BUBBLE, Widget.Kind.HEATMAP] and (
                z := self.get_live_field("z")
            ):
                self.fields["z_aggregator"].choices = [
                    (choice.value, choice.name)
                    for choice in AGGREGATION_TYPE_MAP[schema[z].name]
                ]

    def get_live_fields(self):
        fields = super().get_live_fields()
        table = self.get_live_field("table")

        if table:
            fields += ["sort_by", "sort_ascending", "label", "z", "z_aggregator"]
        return fields


class StackedChartForm(GenericWidgetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        table = self.get_live_field("table")
        schema = Table.objects.get(pk=table).schema if table else None

        if schema:
            columns = [(column, column) for column in schema]
            self.fields["label"].choices = columns
            self.fields["z"].choices = [("", "No column selected"), *columns]
            # Can't overwrite label in Meta because we would have to overwrite the whole thing
            self.fields["z"].label = "Color"
            self.fields["z"].required = False

    def get_live_fields(self):
        fields = super().get_live_fields()
        table = self.get_live_field("table")

        if table:
            fields += [
                "sort_by",
                "sort_ascending",
                "label",
                "z",
                "stack_100_percent",
            ]
        return fields


FORMS = {
    Widget.Kind.TABLE: GenericWidgetForm,
    Widget.Kind.BAR: TwoDimensionForm,
    Widget.Kind.STACKED_COLUMN: StackedChartForm,
    Widget.Kind.COLUMN: TwoDimensionForm,
    Widget.Kind.STACKED_BAR: StackedChartForm,
    Widget.Kind.LINE: TwoDimensionForm,
    Widget.Kind.PIE: TwoDimensionForm,
    Widget.Kind.AREA: TwoDimensionForm,
    Widget.Kind.DONUT: TwoDimensionForm,
    Widget.Kind.SCATTER: TwoDimensionForm,
    Widget.Kind.FUNNEL: TwoDimensionForm,
    Widget.Kind.PYRAMID: TwoDimensionForm,
    Widget.Kind.RADAR: TwoDimensionForm,
    Widget.Kind.HEATMAP: ThreeDimensionForm,
    Widget.Kind.BUBBLE: ThreeDimensionForm,
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

SingleValueFormset = forms.inlineformset_factory(
    Widget,
    AggregationColumn,
    form=AggregationColumnForm,
    can_delete=True,
    extra=0,
    max_num=1,
    formset=RequiredInlineFormset,
)


class WidgetDuplicateForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ()
