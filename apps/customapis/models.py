from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django_cryptography.fields import encrypt
from jsonpath_ng import parse
from jsonpath_ng.parser import JsonPathParserError

from apps.base.clients import SLUG
from apps.base.models import BaseModel
from apps.integrations.models import Integration

MAX_BODY_BINARY_SIZE = 10 * 1024 * 1024


def with_slug(path):
    return f"{SLUG}/{path}" if SLUG else path


def validate_json_path(value):
    try:
        parse(value)
    except JsonPathParserError as exc:
        raise ValidationError(
            "JSONPath expression is not valid: %(exc)s",
            params={"exc": str(exc)},
        )


def validate_body_binary(value):
    if value.size > MAX_BODY_BINARY_SIZE:
        raise ValidationError("The maximum file size that can be uploaded is 10MB")


class CustomApi(BaseModel):
    class HttpRequestMethod(models.TextChoices):
        GET = "GET", "GET"
        HEAD = "HEAD", "HEAD"
        POST = "POST", "POST"
        PUT = "PUT", "PUT"
        DELETE = "DELETE", "DELETE"
        CONNECT = "CONNECT", "CONNECT"
        OPTIONS = "OPTIONS", "OPTIONS"
        TRACE = "TRACE", "TRACE"
        PATCH = "PATCH", "PATCH"

    class Authorization(models.TextChoices):
        NO_AUTH = "no_auth", "No Auth"
        API_KEY = "api_key", "API Key"
        BEARER_TOKEN = "bearer_token", "Bearer Token"
        BASIC_AUTH = "basic_auth", "Basic Auth"
        DIGEST_AUTH = "digest_auth", "Digest Auth"
        OAUTH2 = "oauth2", "OAuth2"

    class ApiKeyAddTo(models.TextChoices):
        HTTP_HEADER = "http_header", "HTTP Header"
        QUERY_PARAMS = "query_params", "Query Params"

    class Body(models.TextChoices):
        NONE = "none", "none"
        FORM_DATA = "form-data", "form-data"
        X_WWW_FORM_URLENCODED = "x-www-form-urlencoded", "x-www-form-urlencoded"
        RAW = "raw", "raw"
        BINARY = "binary", "binary"

    integration = models.OneToOneField(Integration, on_delete=models.CASCADE)

    url = models.URLField(max_length=2048, null=True)
    json_path = models.TextField(default="$", validators=[validate_json_path])

    ndjson_file = models.FileField(upload_to=with_slug("customapi_ndjson"), null=True)

    http_request_method = models.CharField(
        max_length=8, choices=HttpRequestMethod.choices, default=HttpRequestMethod.GET
    )
    authorization = models.CharField(
        max_length=16, choices=Authorization.choices, default=Authorization.NO_AUTH
    )

    # api key
    api_key_key = models.CharField(max_length=8192, null=True)
    api_key_value = encrypt(models.CharField(max_length=8192, null=True))
    api_key_add_to = models.CharField(
        max_length=8192, choices=ApiKeyAddTo.choices, default=ApiKeyAddTo.HTTP_HEADER
    )

    # bearer token
    bearer_token = encrypt(models.CharField(max_length=1024, null=True))

    # basic auth or digest auth
    username = models.CharField(max_length=1024, null=True)
    password = encrypt(models.CharField(max_length=1024, null=True))

    # oauth2
    oauth2 = models.ForeignKey("oauth2.OAuth2", null=True, on_delete=models.SET_NULL)

    body = models.CharField(max_length=32, choices=Body.choices, default=Body.NONE)

    # raw
    body_raw = models.TextField(null=True)

    # binary
    body_binary = models.FileField(
        upload_to=with_slug("customapi_body_binary"),
        validators=[validate_body_binary],
        null=True,
    )

    @property
    def table_id(self):
        return f"customapi_{self.id:09}"

    @property
    def gcs_uri(self):
        return f"gs://{settings.GS_BUCKET_NAME}/{self.ndjson_file.name}"

    def create_integration(self, name, created_by, project):
        integration = Integration.objects.create(
            project=project,
            kind=Integration.Kind.CUSTOMAPI,
            name=name,
            created_by=created_by,
        )
        self.integration = integration


class QueryParam(BaseModel):

    customapi = models.ForeignKey(
        CustomApi, on_delete=models.CASCADE, related_name="queryparams"
    )
    key = models.CharField(max_length=1024)
    value = models.CharField(max_length=1024)


class HttpHeader(BaseModel):

    customapi = models.ForeignKey(
        CustomApi, on_delete=models.CASCADE, related_name="httpheaders"
    )
    key = models.CharField(max_length=8192)
    value = models.CharField(max_length=8192)


class FormDataEntry(BaseModel):
    class Format(models.TextChoices):
        TEXT = "text", "Text"
        FILE = "file", "File"

    customapi = models.ForeignKey(
        CustomApi, on_delete=models.CASCADE, related_name="formdataentries"
    )
    format = models.CharField(max_length=4, choices=Format.choices, default=Format.TEXT)
    key = models.CharField(max_length=8192)
    text = models.CharField(max_length=8192)
    file = models.FileField(
        upload_to=with_slug("formdataentry_file"),
        validators=[validate_body_binary],
        null=True,
    )


class FormURLEncodedEntry(BaseModel):
    customapi = models.ForeignKey(
        CustomApi, on_delete=models.CASCADE, related_name="formurlencodedentries"
    )
    key = models.CharField(max_length=8192)
    value = models.CharField(max_length=8192)
