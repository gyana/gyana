from django.core.files import File
from django_drf_filepond.models import TemporaryUpload

from apps.base.forms import ModelForm

from .models import Upload


class UploadCreateForm(ModelForm):
    class Meta:
        model = Upload
        fields = ["file"]
        labels = {"file": "Choose a file"}
        help_texts = {"file": "Maximum file size is 1GB"}

    def __init__(self, *args, **kwargs):
        self._project = kwargs.pop("project")
        self._created_by = kwargs.pop("created_by")

        super().__init__(*args, **kwargs)

    def pre_save(self, instance):
        self._tu = TemporaryUpload.objects.get(upload_id=self.data["filepond"])
        instance.file = File(self._tu.file)

        instance.create_integration(
            self._tu.upload_name, self._created_by, self._project
        )

    def post_save(self, instance):
        self._tu.delete()


class UploadUpdateForm(ModelForm):
    class Meta:
        model = Upload
        fields = ["file", "field_delimiter"]
        labels = {"file": "Choose a file"}
        help_texts = {
            "file": "Maximum file size is 1GB",
            "field_delimiter": "A field delimiter is a character that separates cells in a CSV table.",
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.fields["file"].required = False
