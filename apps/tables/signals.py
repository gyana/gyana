from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

from apps.base.engine.bigquery import bigquery

from .models import Table


@receiver(post_delete, sender=Table)
def delete_bigquery_table(sender, instance, *args, **kwargs):
    if settings.MOCK_REMOTE_OBJECT_DELETION:
        return

    # hotfix for cloned templates where bq dataset name is invalid
    if " copy " in instance.bq_id:
        return

    bigquery().delete_table(instance.bq_id, not_found_ok=True)
