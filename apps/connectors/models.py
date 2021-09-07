from django.conf import settings
from django.db import models

from apps.base.models import BaseModel
from apps.integrations.models import Integration


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
    # keep track of sync succeeded time from fivetran
    fivetran_succeeded_at = models.DateTimeField(auto_now_add=True)

    # track the celery task
    sync_task_id = models.UUIDField(null=True)
    sync_started = models.DateTimeField(null=True)

    @property
    def fivetran_dashboard_url(self):
        return f"https://fivetran.com/dashboard/connectors/{self.service}/{self.schema}?requiredGroup={settings.FIVETRAN_GROUP}"
