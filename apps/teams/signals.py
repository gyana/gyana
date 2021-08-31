from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

from apps.base.clients import bigquery_client

from .models import Team


@receiver(post_delete, sender=Team)
def delete_bigquery_dataset(sender, instance, *args, **kwargs):
    if settings.MOCK_REMOTE_OBJECT_DELETION:
        return

    bigquery_client().delete_dataset(
        instance.tables_dataset_id, delete_contents=True, not_found_ok=True
    )
