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
