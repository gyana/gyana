from django import forms

from .models import Widget


class WidgetForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ['name']
