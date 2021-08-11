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

    fivetran_authorized = models.BooleanField(default=False)
    fivetran_poll_historical_sync_task_id = models.UUIDField(null=True)
    historical_sync_complete = models.BooleanField(default=False)
    last_synced = models.DateTimeField(null=True)
