from django.conf import settings
from django.db import models
from django.db.models.fields import related

from apps.base.clients import SLUG
from apps.base.models import BaseModel
from apps.integrations.models import Integration


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

    class ApiKeyAddTo(models.TextChoices):
        HTTP_HEADER = "http_header", "HTTP Header"
        QUERY_PARAMS = "query_params", "Query Params"

    integration = models.OneToOneField(Integration, on_delete=models.CASCADE)

    url = models.URLField(max_length=2048)
    json_path = models.TextField(default="$")

    ndjson_file = models.FileField(
        upload_to=f"{SLUG}/custom_api_jsonnl" if SLUG else "custom_api_ndjson",
        null=True,
    )

    http_request_method = models.CharField(
        max_length=8, choices=HttpRequestMethod.choices, default=HttpRequestMethod.GET
    )
    authorization = models.CharField(
        max_length=16, choices=Authorization.choices, default=Authorization.NO_AUTH
    )

    # api key
    api_key_key = models.CharField(max_length=8192, null=True)
    api_key_value = models.CharField(max_length=8192, null=True)
    api_key_add_to = models.CharField(
        max_length=8192, choices=ApiKeyAddTo.choices, default=ApiKeyAddTo.HTTP_HEADER
    )

    # bearer token
    bearer_token = models.CharField(max_length=1024, null=True)

    # basic auth or digest auth
    username = models.CharField(max_length=1024, null=True)
    password = models.CharField(max_length=1024, null=True)

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
