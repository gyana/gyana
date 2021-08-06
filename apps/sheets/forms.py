from django import forms

from .models import Sheet


class SheetForm(forms.ModelForm):
    class Meta:
        model = Sheet
        fields = ['name']
