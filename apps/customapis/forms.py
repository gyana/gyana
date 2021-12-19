from functools import cache

from django import forms
from django.urls import reverse
from django.utils.html import mark_safe

from apps.base.forms import BaseModelForm
from apps.base.formsets import RequiredInlineFormset
from apps.base.live_update_form import LiveUpdateForm
from apps.base.widgets import DatalistInput

from .models import CustomApi, HttpHeader, QueryParam

HEADERS_PATH = "apps/customapis/headers.txt"

AUTHORIZATION_TO_FIELDS = {
    CustomApi.Authorization.NO_AUTH: [],
    CustomApi.Authorization.API_KEY: [
        "api_key_key",
        "api_key_value",
        "api_key_add_to",
    ],
    CustomApi.Authorization.BEARER_TOKEN: ["bearer_token"],
    CustomApi.Authorization.BASIC_AUTH: ["username", "password"],
    CustomApi.Authorization.DIGEST_AUTH: ["username", "password"],
    CustomApi.Authorization.OAUTH2: ["oauth2"],
}


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


class CustomApiUpdateForm(LiveUpdateForm):
    class Meta:
        model = CustomApi
        fields = [
            "url",
            "json_path",
            "http_request_method",
            "authorization",
            "api_key_key",
            "api_key_value",
            "api_key_add_to",
            "bearer_token",
            "username",
            "password",
            "oauth2",
        ]
        labels = {
            "url": "URL",
            "json_path": "JSON Path",
            "http_request_method": "HTTP Request Method",
            "api_key_key": "Key",
            "api_key_value": "Value",
            "api_key_add_to": "Add To",
            "oauth2": "OAuth2",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.get_live_field("authorization") == CustomApi.Authorization.OAUTH2:
            field = self.fields["oauth2"]
            project = self.instance.integration.project

            field.queryset = project.oauth2_set.filter(token__isnull=False).all()
            settings_url = reverse("projects:update", args=(project.id,))
            field.help_text = mark_safe(
                f'You can authorize services with OAuth2 in your project <a href="{settings_url}" class="link">settings</a>'
            )

    def get_live_fields(self):
        live_fields = ["url", "json_path", "http_request_method", "authorization"]
        live_fields += AUTHORIZATION_TO_FIELDS[self.get_live_field("authorization")]
        return live_fields

    def get_live_formsets(self):
        return [QueryParamFormset, HttpHeaderFormset]
