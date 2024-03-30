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
        # todo: understand why this is required
        instance.file = self.files["file"]
        instance.create_integration(instance.file.name, self._created_by, self._project)


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
