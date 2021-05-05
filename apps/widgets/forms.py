from apps.datasets.models import Dataset
from django import forms
from django.forms.widgets import HiddenInput

from .models import Widget


class WidgetForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ["name", "dashboard", "dataset"]
        widgets = {"dashboard": HiddenInput()}

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields["dataset"].queryset = Dataset.objects.filter(project=project)


class WidgetConfigForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ["kind", "label", "value"]

    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660
        self.columns = kwargs.pop("columns")
        super().__init__(*args, **kwargs)
        self.fields["label"].choices = self.columns
        self.fields["value"].choices = self.columns

    label = forms.ChoiceField(choices=())
    value = forms.ChoiceField(choices=())
