from django import forms

from .models import Dataset


class DatasetForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ["name", "url"]
        help_texts = {
            "url": "Needs to be public (TODO: share with service account)",
        }
