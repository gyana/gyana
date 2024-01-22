from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

from apps.base.clients import get_engine

from .models import Table


@receiver(post_delete, sender=Table)
def delete_engine_table(sender, instance, *args, **kwargs):
    if settings.MOCK_REMOTE_OBJECT_DELETION:
        return

    # hotfix for cloned templates where bq dataset name is invalid
    if " copy " in instance.fqn:
        return

    # TODO: Make sure it works for postgres backend
    get_engine().drop_table(instance.fqn)
