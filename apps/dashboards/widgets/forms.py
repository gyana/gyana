from django import forms
from django.forms.widgets import HiddenInput

from .models import Widget


class WidgetForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ["name", "dashboard", "dataset"]
        widgets = {"dashboard": HiddenInput()}


class WidgetConfigForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ["kind", "label", "value"]
