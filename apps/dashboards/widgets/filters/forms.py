from django import forms
from django.forms.widgets import HiddenInput

from .models import Filter


class FilterForm(forms.ModelForm):
    class Meta:
        model = Filter
        fields = ["widget", "column"]
        widgets = {"widget": HiddenInput()}

    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660
        self.columns = kwargs.pop("columns")
        super().__init__(*args, **kwargs)
        self.fields["column"].choices = self.columns

    column = forms.ChoiceField(choices=())
