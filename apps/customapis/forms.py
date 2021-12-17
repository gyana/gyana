from django import forms

from apps.base.forms import BaseModelForm
from apps.base.formsets import RequiredInlineFormset

from .models import CustomApi, QueryParam


class QueryParamForm(BaseModelForm):
    class Meta:
        model = QueryParam
        fields = ["key", "value"]


QueryParamFormset = forms.inlineformset_factory(
    CustomApi,
    QueryParam,
    form=QueryParamForm,
    can_delete=True,
    extra=0,
    formset=RequiredInlineFormset,
)


class CustomApiCreateForm(BaseModelForm):
    name = forms.CharField(max_length=255)

    class Meta:
        model = CustomApi
        fields = ["url"]
        labels = {"url": "URL"}

    def __init__(self, *args, **kwargs):
        self._project = kwargs.pop("project")
        self._created_by = kwargs.pop("created_by")
        super().__init__(*args, **kwargs)

    def pre_save(self, instance):
        instance.create_integration(
            self.cleaned_data["name"], self._created_by, self._project
        )

    def post_save(self, instance):
        instance.integration.project.update_schedule()


class CustomApiUpdateForm(BaseModelForm):
    class Meta:
        model = CustomApi
        fields = ["url", "json_path", "http_request_method"]
        labels = {
            "url": "URL",
            "json_path": "JSON Path",
            "http_request_method": "HTTP Request Method",
        }

    def get_live_formsets(self):
        return [QueryParamFormset]
