import textwrap
from os.path import splitext

from apps.integrations.models import Integration
from apps.uploads.widgets import GCSFileUpload
from django import forms
from django.db import transaction

from .models import Upload


class UploadCreateForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = ["file_gcs_path"]
        widgets = {
            "file_gcs_path": GCSFileUpload(),
        }
        labels = {"file_gcs_path": "Upload a file"}

    def __init__(self, *args, **kwargs):
        self._project = kwargs.pop("project")
        self._created_by = kwargs.pop("created_by")

        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)

        # file_gcs_path has an extra hidden input
        name = textwrap.shorten(
            splitext(self.data["file_name"])[0], width=255, placeholder="..."
        )
        integration = Integration(
            project=self._project,
            kind=Integration.Kind.UPLOAD,
            name=name,
            created_by=self._created_by,
        )
        instance.integration = integration

        if commit:
            with transaction.atomic():
                integration.save()
                instance.save()
                self.save_m2m()

        return instance


class UploadUpdateForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = ["field_delimiter"]
        help_texts = {
            "field_delimiter": "A field delimiter is a character that separates cells in a CSV table."
        }
