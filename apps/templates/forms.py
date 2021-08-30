from django import forms

from .models import Template


class TemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = []
