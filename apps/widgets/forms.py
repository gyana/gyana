from apps.filters.forms import FilterForm
from apps.filters.models import Filter
from apps.nodes.widgets import SourceSelect
from apps.tables.models import Table
from apps.utils.live_update_form import LiveUpdateForm
from apps.utils.schema_form_mixin import SchemaFormMixin
from apps.widgets.widgets import VisualSelect
from django import forms
from django.forms.models import BaseInlineFormSet

from .models import MULTI_VALUES_CHARTS, MultiValues, Widget


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
            "aggregator",
            "value",
            "z",
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
            self.fields["table"].queryset = Table.objects.filter(
                project=project
            ).exclude(source="intermediate_node")

    def get_live_fields(self):
        return ["table", "kind", "name"]

    def get_live_formsets(self):
        formsets = [FilterFormset]
        if self.instance.kind not in [
            Widget.Kind.TABLE,
            Widget.Kind.FUNNEL,
            Widget.Kind.PYRAMID,
            Widget.Kind.PIE,
            Widget.Kind.BUBBLE,
            Widget.Kind.DONUT,
            Widget.Kind.HEATMAP,
            Widget.Kind.STACKED_BAR,
            Widget.Kind.STACKED_COLUMN,
        ]:
            formsets += [ValueFormset]
        return formsets


class TwoDimensionForm(GenericWidgetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        table = self.get_live_field("table")
        schema = Table.objects.get(pk=table).schema if table else None

        if schema and "label" in self.fields:
            columns = [(column, column) for column in schema]
            self.fields["label"].choices = columns
            self.fields["value"].choices = columns

    def get_live_fields(self):
        fields = super().get_live_fields()
        table = self.get_live_field("table")

        if table:
            fields += ["sort_by", "sort_ascending", "label", "aggregator", "value"]
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

    def get_live_fields(self):
        fields = super().get_live_fields()
        table = self.get_live_field("table")

        if table:
            fields += [
                "sort_by",
                "sort_ascending",
                "label",
                "aggregator",
                "z",
            ]
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
                "aggregator",
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


class ValueForm(SchemaFormMixin, LiveUpdateForm):
    column = forms.ChoiceField(choices=())

    class Meta:
        model = MultiValues
        fields = ("column",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.schema:
            self.fields["column"] = forms.ChoiceField(
                choices=[(column, column) for column in self.schema]
            )


class RequiredInlineFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False
            form.use_required_attribute = True


FilterFormset = forms.inlineformset_factory(
    Widget,
    Filter,
    form=FilterForm,
    can_delete=True,
    extra=0,
    formset=RequiredInlineFormset,
)

ValueFormset = forms.inlineformset_factory(
    Widget, MultiValues, form=ValueForm, can_delete=True, extra=0
)


class WidgetDuplicateForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ()
