from apps.base.models import BaseModel
from apps.integrations.models import Integration
from django.db import models


class Connector(BaseModel):

    integration = models.OneToOneField(
        Integration,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    # todo: which of these do not need to be null
    service = models.TextField(
        max_length=255,
        null=True,
        help_text="Name of the Fivetran service, uses keys from services.yaml as value",
    )
    fivetran_id = models.TextField(
        null=True,
        help_text="ID of the connector in Fivetran, crucial to link this Integration to the Fivetran connector",
    )
    schema = models.TextField(
        null=True,
        help_text="The schema name under which Fivetran saves the data in BigQuery. It also is the name of the schema maintained by Fivetran in their systems.",
    )
    fivetran_authorized = models.BooleanField(default=False)
    fivetran_poll_historical_sync_task_id = models.UUIDField(null=True)
    historical_sync_complete = models.BooleanField(default=False)
    last_synced = models.DateTimeField(null=True)
