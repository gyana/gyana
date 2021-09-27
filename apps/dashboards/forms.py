from django import forms
from django.forms.widgets import HiddenInput

from .models import Dashboard


class DashboardFormCreate(forms.ModelForm):
    class Meta:
        model = Dashboard
        fields = ["project"]
        widgets = {"project": HiddenInput()}


class DashboardForm(forms.ModelForm):
    name = forms.CharField(required=False)
    width = forms.IntegerField(required=False)
    height = forms.IntegerField(required=False)

    class Meta:
        model = Dashboard
        fields = ["name", "width", "height"]
