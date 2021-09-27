from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

from apps.base.clients import bigquery_client, fivetran_client
from apps.connectors.config import get_services
from apps.connectors.fivetran import FivetranClientError

from .models import Connector


@receiver(post_delete, sender=Connector)
def delete_fivetran_connector(sender, instance, *args, **kwargs):
    if settings.MOCK_REMOTE_OBJECT_DELETION:
        return

    try:

        datasets = {
            s.name_in_destination for s in fivetran_client().get_schemas(instance)
        }

        # fivetran schema config does not include schema prefix for databases
        if get_services()[instance.service]["requires_schema_prefix"] == "t":
            datasets = {f"{instance.schema}_{id_}" for id_ in datasets}

        for dataset in datasets:
            bigquery_client().delete_dataset(
                dataset, delete_contents=True, not_found_ok=True
            )

        fivetran_client().delete(instance)

    except FivetranClientError as e:
        print(e)
