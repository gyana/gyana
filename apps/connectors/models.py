from apps.base.models import BaseModel
from apps.integrations.models import Integration
from django.db import models


class Connector(BaseModel):

    integration = models.OneToOneField(Integration, on_delete=models.CASCADE)

    # service name, see services.yaml
    service = models.TextField(max_length=255)
    # unique identifier for API requests in fivetran
    fivetran_id = models.TextField()
    # schema or schema_prefix for storage in bigquery
    schema = models.TextField()

    # do not display unfinished connectors that are not authorized as pending
    # we delete along with corresponding Fivetran model
    fivetran_authorized = models.BooleanField(default=False)

    # track the celery task
    sync_task_id = models.UUIDField(null=True)
    sync_started = models.DateTimeField(null=True)
