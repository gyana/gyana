from django import forms

from .models import Run


class RunForm(forms.ModelForm):
    class Meta:
        model = Run
        fields = []
