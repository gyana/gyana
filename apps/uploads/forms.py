import textwrap
from os.path import splitext

from apps.uploads.widgets import GCSFileUpload
from django import forms
from django.db import transaction
from django.forms.widgets import HiddenInput

from .models import Upload


class UploadCreateForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = ["project", "file_gcs_path"]
        widgets = {
            "project": HiddenInput(),
            "file_gcs_path": GCSFileUpload(),
        }
        labels = {"file_gcs_path": "Upload a file"}

    def save(self, commit=True):
        instance = super().save(commit=False)
        # file_gcs_path has an extra hidden input
        instance.file_name = textwrap.shorten(
            splitext(self.data["file_name"])[0], width=255, placeholder="..."
        )

        if commit:
            with transaction.atomic():
                instance.save()
                self.save_m2m()

        return instance
