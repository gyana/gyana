from apps.base.forms import BaseModelForm

from .models import CustomApi


class CustomApiCreateForm(BaseModelForm):
    class Meta:
        model = CustomApi
        fields = ["url", "json_path"]
        labels = {"url": "URL", "json_path": "JSON Path"}

    def __init__(self, *args, **kwargs):
        self._project = kwargs.pop("project")
        self._created_by = kwargs.pop("created_by")
        super().__init__(*args, **kwargs)

    def pre_save(self, instance):
        instance.create_integration("API", self._created_by, self._project)

    def post_save(self, instance):
        instance.integration.project.update_schedule()


class CustomApiUpdateForm(BaseModelForm):
    class Meta:
        model = CustomApi
        fields = []
