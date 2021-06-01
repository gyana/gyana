from apps.tables.models import Table
from django import forms
from django.forms.widgets import HiddenInput

from .models import Widget


class LiveForm(forms.ModelForm):
    live = forms.CharField(widget=forms.HiddenInput(), required=True)

    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660
        remove_live = kwargs.pop("remove-live", None)

        super().__init__(*args, **kwargs)

        live_fields = self.get_live_fields()

        if not remove_live:
            live_fields += ["live"]

        self.fields = {k: v for k, v in self.fields.items() if k in live_fields}

    def get_live_field(self, name):

        # data populated by POST request in update
        if name in self.data:
            return self.data[name]

        # data populated from database
        return self.initial[name]

    def get_live_fields(self):
        raise NotImplementedError()


class WidgetConfigForm(LiveForm):

    label = forms.ChoiceField(choices=())
    value = forms.ChoiceField(choices=())

    class Meta:
        model = Widget
        fields = ["description", "table", "kind", "label", "aggregator", "value"]

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
