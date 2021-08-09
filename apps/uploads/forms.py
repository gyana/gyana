from os.path import splitext

from apps.integrations.models import Integration
from apps.uploads.widgets import GCSFileUpload
from django import forms
from django.db import transaction
from django.forms.widgets import HiddenInput

from .models import Upload


class CSVForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name", "kind", "project"]
        widgets = {
            "kind": HiddenInput(),
            "project": HiddenInput(),
        }


class UploadCreateForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = ["project", "file_gcs_path"]
        widgets = {
            "project": HiddenInput(),
            "file_gcs_path": GCSFileUpload(attrs={"accept": ".csv"}),
        }
        labels = {"file_gcs_path": "Upload a file"}

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.file_name = splitext(self.data["name"])[0]

        if commit:
            with transaction.atomic():
                instance.save()
                self.save_m2m()

        return instance
