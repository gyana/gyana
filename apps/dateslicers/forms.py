from django import forms

from .models import DateSlicer


class DateSlicerForm(forms.ModelForm):
    class Meta:
        model = DateSlicer
        fields = ['name']
