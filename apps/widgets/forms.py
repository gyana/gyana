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


class WidgetConfigForm(LiveUpdateForm):

    label = forms.ChoiceField(choices=())
    z = forms.ChoiceField(choices=())

    class Meta:
        model = Widget
        fields = ["description", "table", "kind", "label", "aggregator", "z"]
        widgets = {"kind": VisualSelect(), "table": SourceSelect()}

    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660
        project = kwargs.pop("project", None)

        super().__init__(*args, **kwargs)

        table = self.get_live_field("table")
        schema = Table.objects.get(pk=table).schema if table else None

        if project:
            self.fields["table"].queryset = Table.objects.filter(
                project=project
            ).exclude(source="intermediate_node")

        if schema and "label" in self.fields:
            columns = [(column, column) for column in schema]
            self.fields["label"].choices = columns
            if "z" in self.fields:
                self.fields["z"].choices = columns

    def get_live_fields(self):

        fields = ["table", "kind", "description"]

        table = self.get_live_field("table")
        kind = self.get_live_field("kind")

        if table and kind and kind != Widget.Kind.TABLE:
            fields += [
                "label",
                "aggregator",
            ]

            if kind in [Widget.Kind.BUBBLE, Widget.Kind.HEATMAP]:
                fields += ["z"]

        return fields


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
