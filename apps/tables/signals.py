from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

from apps.base.engine import get_backend_client

from .models import Table


@receiver(post_delete, sender=Table)
def delete_backend_table(sender, instance, *args, **kwargs):
    if settings.MOCK_REMOTE_OBJECT_DELETION:
        return

    # hotfix for cloned templates where bq dataset name is invalid
    if " copy " in instance.bq_id:
        return
    # TODO: Make sure it works for postgres backend
    get_backend_client().client.drop_table(instance.bq_id, False=True)
