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
        columns = kwargs.pop("columns", None)
        project = kwargs.pop("project", None)

        super().__init__(*args, **kwargs)

        self.fields["label"].choices = columns
        self.fields["value"].choices = columns

        if project:
            self.fields["table"].queryset = Table.objects.filter(project=project)

    label = forms.ChoiceField(choices=())
    value = forms.ChoiceField(choices=())
