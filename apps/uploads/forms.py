from apps.integrations.models import Integration
from apps.uploads.widgets import GCSFileUpload
from django import forms
from django.db import transaction
from django.forms.widgets import HiddenInput
from pathvalidate import ValidationError as PathValidationError
from pathvalidate import validate_filename

from .models import Upload


class CSVForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name", "kind", "project"]
        widgets = {
            "kind": HiddenInput(),
            "project": HiddenInput(),
        }


class CSVCreateForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = ["name", "project"]
        widgets = {
            "project": HiddenInput(),
            "name": HiddenInput(),
        }

    file = forms.CharField(
        widget=GCSFileUpload(attrs={"accept": ".csv"}),
    )

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.name = self.cleaned_data["file"].split(".").pop(0)

        if commit:
            with transaction.atomic():
                instance.save()
                self.save_m2m()

        return instance
