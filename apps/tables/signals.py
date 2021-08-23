from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from google.api_core.exceptions import NotFound

from apps.base.clients import bigquery_client

from .models import Table


@receiver(post_delete, sender=Table)
def delete_bigquery_table(sender, instance, *args, **kwargs):
    # don't delete tables for our cypress fixtures
    if instance.bq_dataset.startswith("cypress_"):
        return

    bigquery_client().delete_table(instance.bq_obj, not_found_ok=True)
