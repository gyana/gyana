from functools import cache

from django import forms

from apps.base.forms import BaseModelForm
from apps.base.formsets import RequiredInlineFormset
from apps.base.widgets import DatalistInput

from .models import CustomApi, HttpHeader, QueryParam

HEADERS_PATH = "apps/customapis/headers.txt"


@cache
def get_headers():
    with open(HEADERS_PATH, "r") as f:
        return f.read().split("\n")


class QueryParamForm(BaseModelForm):
    class Meta:
        model = QueryParam
        fields = ["key", "value"]
        help_texts = {"key": "KEY", "value": "VALUE"}


QueryParamFormset = forms.inlineformset_factory(
    CustomApi,
    QueryParam,
    form=QueryParamForm,
    can_delete=True,
    extra=0,
    formset=RequiredInlineFormset,
)


class HttpHeaderForm(BaseModelForm):
    class Meta:
        model = HttpHeader
        fields = ["key", "value"]
        help_texts = {"key": "KEY", "value": "VALUE"}
        widgets = {"key": DatalistInput(options=get_headers())}


HttpHeaderFormset = forms.inlineformset_factory(
    CustomApi,
    HttpHeader,
    form=HttpHeaderForm,
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
        return [QueryParamFormset, HttpHeaderFormset]
