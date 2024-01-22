from apps.base.forms import ModelForm
from apps.uploads.widgets import GCSFileUpload

from .models import Upload


class UploadCreateForm(ModelForm):
    class Meta:
        model = Upload
        fields = ["file_gcs_path"]
        widgets = {"file_gcs_path": GCSFileUpload()}
        labels = {"file_gcs_path": "Choose a file"}
        help_texts = {"file_gcs_path": "Maximum file size is 1GB"}

    def __init__(self, *args, **kwargs):
        self._project = kwargs.pop("project")
        self._created_by = kwargs.pop("created_by")

        super().__init__(*args, **kwargs)

    def pre_save(self, instance):
        instance.create_integration(
            self.data["file_name"], self._created_by, self._project
        )


class UploadUpdateForm(ModelForm):
    class Meta:
        model = Upload
        fields = ["file_gcs_path", "field_delimiter"]
        widgets = {"file_gcs_path": GCSFileUpload()}
        labels = {"file_gcs_path": "Choose a file"}
        help_texts = {
            "file_gcs_path": "Maximum file size is 1GB",
            "field_delimiter": "A field delimiter is a character that separates cells in a CSV table.",
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.fields["file_gcs_path"].required = False
