from django import forms

from .models import Export


class ExportForm(forms.ModelForm):
    class Meta:
        model = Export
        fields = ['name']
