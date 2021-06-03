from apps.filters.forms import FilterForm
from apps.filters.models import Filter
from apps.tables.models import Table
from apps.utils.live_update_form import LiveUpdateForm
from apps.widgets.widgets import VisualSelect
from apps.workflows.widgets import SourceSelect
from django import forms

from .models import Widget


class WidgetConfigForm(LiveUpdateForm):

    label = forms.ChoiceField(choices=())
    value = forms.ChoiceField(choices=())

    class Meta:
        model = Widget
        fields = ["description", "table", "kind", "label", "aggregator", "value"]
        widgets = {"kind": VisualSelect(), "table": SourceSelect()}

    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660
        project = kwargs.pop("project", None)

        super().__init__(*args, **kwargs)

        table = self.get_live_field("table")
        schema = Table.objects.get(pk=table).schema if table else None

        if project:
            self.fields["table"].queryset = Table.objects.filter(project=project)

        if schema and "label" in self.fields:
            columns = [(column, column) for column in schema]
            self.fields["label"].choices = columns
            self.fields["value"].choices = columns

    def get_live_fields(self):

        fields = ["table", "kind", "description"]

        table = self.get_live_field("table")
        kind = self.get_live_field("kind")

        if table and kind and kind != Widget.Kind.TABLE:
            fields += ["label", "aggregator", "value"]

        return fields


FilterFormset = forms.inlineformset_factory(
    Widget, Filter, form=FilterForm, can_delete=True, extra=1
)
