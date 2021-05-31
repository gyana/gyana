from apps.tables.models import Table
from django import forms
from django.forms.widgets import HiddenInput

from .models import Widget


class WidgetConfigForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ["table", "kind", "aggregator", "label", "value", "description"]

    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660
        project = kwargs.pop("project", None)
        schema = kwargs.pop("schema", None)

        super().__init__(*args, **kwargs)

        if project:
            self.fields["table"].queryset = Table.objects.filter(project=project)

        if schema:
            columns = [(column, column) for column in schema]
            self.fields["label"].choices = columns
            self.fields["value"].choices = columns

    label = forms.ChoiceField(choices=())
    value = forms.ChoiceField(choices=())
