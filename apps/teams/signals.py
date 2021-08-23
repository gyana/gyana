from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from google.api_core.exceptions import NotFound

from apps.base.clients import bigquery_client

from .models import Team


@receiver(post_delete, sender=Team)
def delete_bigquery_dataset(sender, instance, *args, **kwargs):
    # don't delete datasets for our cypress fixtures
    if instance.tables_dataset_id.startswith("cypress_"):
        return

    bigquery_client().delete_dataset(instance.tables_dataset_id, not_found_ok=True)
