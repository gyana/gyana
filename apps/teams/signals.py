from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

from apps.base.engine import get_backend_client

from .models import Team


@receiver(post_delete, sender=Team)
def delete_backend_dataset(sender, instance, *args, **kwargs):
    if settings.MOCK_REMOTE_OBJECT_DELETION:
        return

    get_backend_client().delete_team_dataset(instance)
