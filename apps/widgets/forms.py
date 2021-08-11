from apps.base.aggregations import AGGREGATION_TYPE_MAP
from apps.base.live_update_form import LiveUpdateForm
from apps.columns.forms import FunctionColumnForm
from apps.columns.models import FunctionColumn
from apps.filters.forms import FilterForm
from apps.filters.models import Filter
from apps.tables.models import Table
from django import forms
from django.forms.models import BaseInlineFormSet

from .models import Widget
from .widgets import SourceSelect, VisualSelect


class GenericWidgetForm(LiveUpdateForm):
    label = forms.ChoiceField(choices=())
    value = forms.ChoiceField(choices=())
    z = forms.ChoiceField(choices=())

    class Meta:
        model = Widget
        fields = [
            "name",
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
        return ["table", "kind", "name"]

    def get_live_formsets(self):
        if self.get_live_field("table") is None:
            return []

        formsets = [FilterFormset]
        if self.instance.kind not in [Widget.Kind.TABLE]:
            formsets += [FunctionColumnFormset]
        return formsets


class TwoDimensionForm(GenericWidgetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        table = self.get_live_field("table")
        schema = Table.objects.get(pk=table).schema if table else None

        if schema and "label" in self.fields:
            columns = [(column, column) for column in schema]
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
            self.fields["z"].label = "Colour"
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


class RequiredInlineFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False
            form.use_required_attribute = True


class InlineColumnFormset(RequiredInlineFormset):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.form.base_fields["column"] = forms.ChoiceField(
            choices=[
                ("", "No column selected"),
                *[(col, col) for col in self.instance.table.schema],
            ]
        )


FilterFormset = forms.inlineformset_factory(
    Widget,
    Filter,
    form=FilterForm,
    can_delete=True,
    extra=0,
    formset=RequiredInlineFormset,
)

FunctionColumnFormset = forms.inlineformset_factory(
    Widget,
    FunctionColumn,
    form=FunctionColumnForm,
    can_delete=True,
    extra=0,
    formset=InlineColumnFormset,
)


class WidgetDuplicateForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ()
