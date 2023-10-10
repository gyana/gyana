import json

from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

from .bigquery import delete_team_dataset
from .models import Team


@receiver(post_delete, sender=Team)
def delete_bigquery_dataset(sender, instance, *args, **kwargs):
    if settings.MOCK_REMOTE_OBJECT_DELETION:
        return

    delete_team_dataset(instance)
