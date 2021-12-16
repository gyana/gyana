from django.db import models

from apps.base.clients import SLUG
from apps.base.models import BaseModel
from apps.integrations.models import Integration


class CustomApi(BaseModel):
    integration = models.OneToOneField(Integration, on_delete=models.CASCADE)

    url = models.URLField()
    json_path = models.TextField(default="$")

    ndjson_file = models.FileField(
        upload_to=f"{SLUG}/custom_api_jsonnl" if SLUG else "custom_api_ndjson",
        null=True,
    )

    def create_integration(self, title, created_by, project):
        integration = Integration.objects.create(
            project=project,
            kind=Integration.Kind.API,
            name=title,
            created_by=created_by,
        )
        self.integration = integration
