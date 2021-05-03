from django import forms

from .models import Filter


class FilterForm(forms.ModelForm):
    class Meta:
        model = Filter
        fields = ['name']
