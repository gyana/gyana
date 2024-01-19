from functools import cache

from crispy_forms.bootstrap import TabHolder
from crispy_forms.layout import Layout
from django import forms
from django.urls import reverse
from django.utils.html import mark_safe

from apps.base.account import is_scheduled_help_text
from apps.base.crispy import CrispyFormset, Tab
from apps.base.forms import BaseModelForm, LiveAlpineModelForm, LiveFormsetMixin
from apps.base.formsets import RequiredInlineFormset
from apps.base.widgets import DatalistInput

from .models import (
    CustomApi,
    FormDataEntry,
    FormURLEncodedEntry,
    HttpHeader,
    QueryParam,
)

HEADERS_PATH = "apps/customapis/requests/headers.txt"


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


class FormDataEntryForm(BaseModelForm):
    class Meta:
        model = FormDataEntry
        fields = ["format", "key", "text", "file"]
        show = {
            "text": f"format == '{FormDataEntry.Format.TEXT}'",
            "file": f"format == '{FormDataEntry.Format.FILE}'",
        }
        help_texts = {"format": "Format", "key": "Key", "text": "Text", "file": "File"}


FormDataEntryFormset = forms.inlineformset_factory(
    CustomApi,
    FormDataEntry,
    form=FormDataEntryForm,
    can_delete=True,
    extra=0,
    formset=RequiredInlineFormset,
)

FormDataEntryFormset.show = f"body == '{CustomApi.Body.FORM_DATA}'"


class FormURLEncodedEntryForm(BaseModelForm):
    class Meta:
        model = FormURLEncodedEntry
        fields = ["key", "value"]
        help_texts = {"key": "Key", "value": "Value"}


FormURLEncodedEntryFormset = forms.inlineformset_factory(
    CustomApi,
    FormURLEncodedEntry,
    form=FormURLEncodedEntryForm,
    can_delete=True,
    extra=0,
    formset=RequiredInlineFormset,
)

FormURLEncodedEntryFormset.show = f"body == '{CustomApi.Body.X_WWW_FORM_URLENCODED}'"


class CustomApiCreateForm(BaseModelForm):
    name = forms.CharField(
        max_length=255,
        help_text="E.g. the domain or website, to help you find it later",
    )
    is_scheduled = forms.BooleanField(
        required=False, label="Automatically sync new data"
    )

    class Meta:
        model = CustomApi
        fields = []

    def __init__(self, *args, **kwargs):
        self._project = kwargs.pop("project")
        self._created_by = kwargs.pop("created_by")
        super().__init__(*args, **kwargs)

        is_scheduled_help_text(self.fields["is_scheduled"], self._project)

    def pre_save(self, instance):
        instance.create_integration(
            self.cleaned_data["name"],
            self._created_by,
            self._project,
            self.cleaned_data["is_scheduled"],
        )

    def post_save(self, instance):
        instance.integration.project.update_schedule()


class CustomApiUpdateForm(LiveFormsetMixin, LiveAlpineModelForm):
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
            "body",
            "body_raw",
            "body_binary",
        ]
        formsets = {
            "queryparams": QueryParamFormset,
            "httpheaders": HttpHeaderFormset,
            "formdataentries": FormDataEntryFormset,
            "formurlencodedentries": FormURLEncodedEntryFormset,
        }
        show = {
            "api_key_key": f"authorization == '{CustomApi.Authorization.API_KEY}'",
            "api_key_value": f"authorization == '{CustomApi.Authorization.API_KEY}'",
            "api_key_add_to": f"authorization == '{CustomApi.Authorization.API_KEY}'",
            "bearer_token": f"authorization == '{CustomApi.Authorization.BEARER_TOKEN}'",
            "username": f"authorization == '{CustomApi.Authorization.BASIC_AUTH}' || authorization == '{CustomApi.Authorization.DIGEST_AUTH}'",
            "password": f"authorization == '{CustomApi.Authorization.BASIC_AUTH}' || authorization == '{CustomApi.Authorization.DIGEST_AUTH}'",
            "oauth2": f"authorization == '{CustomApi.Authorization.OAUTH2}'",
            "body_raw": f"body == '{CustomApi.Body.RAW}'",
            "body_binary": f"body == '{CustomApi.Body.BINARY}'",
            "formdataentries": f"body == '{CustomApi.Body.FORM_DATA}'",
            "formurlencodedentries": f"body == '{CustomApi.Body.X_WWW_FORM_URLENCODED}'",
        }
        widgets = {
            "api_key_value": forms.PasswordInput(render_value=True),
            "bearer_token": forms.PasswordInput(render_value=True),
            "password": forms.PasswordInput(render_value=True),
        }
        labels = {
            "url": "URL",
            "json_path": "JSON Path",
            "http_request_method": "HTTP Request Method",
            "api_key_key": "Key",
            "api_key_value": "Value",
            "api_key_add_to": "Add To",
            "oauth2": "OAuth2",
            "body_raw": "Raw",
            "body_binary": "Binary",
        }
        help_texts = {
            "json_path": mark_safe(
                'Extract part of the JSON result, e.g. under a specific key <a href="https://github.com/json-path/JSONPath#operators" class="link">learn more</a>'
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            TabHolder(
                Tab("General", "url", "json_path", "http_request_method"),
                Tab(
                    "Auth",
                    "authorization",
                    "api_key_key",
                    "api_key_value",
                    "api_key_add_to",
                    "bearer_token",
                    "username",
                    "password",
                    "oauth2",
                ),
                Tab(
                    "Params",
                    CrispyFormset("queryparams", "Query Params"),
                ),
                Tab(
                    "Headers",
                    CrispyFormset("httpheaders", "HTTP Headers"),
                ),
                Tab(
                    "Body",
                    "body",
                    "body_raw",
                    "body_binary",
                    CrispyFormset("formdataentries", "Form Data"),
                    CrispyFormset("formurlencodedentries", "Form URL Encoded"),
                ),
            )
        )

        self.fields["url"].required = True

        if "oauth" in self.fields:
            field = self.fields["oauth2"]
            project = self.instance.integration.project

            field.queryset = project.oauth2_set.filter(token__isnull=False).all()
            settings_url = reverse("projects:update", args=(project.id,))
            field.help_text = mark_safe(
                f'You can authorize services with OAuth2 in your project <a href="{settings_url}" class="link">settings</a>'
            )
