import json

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch.dispatcher import receiver
from djpaddle.models import Checkout

from .bigquery import delete_team_dataset
from .models import Team


@receiver(post_delete, sender=Team)
def delete_bigquery_dataset(sender, instance, *args, **kwargs):
    if settings.MOCK_REMOTE_OBJECT_DELETION:
        return

    delete_team_dataset(instance)


@receiver(post_save, sender=Checkout)
def link_checkout_to_team(sender, instance, *args, **kwargs):
    team_id = json.loads(instance.passthrough)["team_id"]
    team = Team.objects.get(pk=team_id)
    team.last_checkout = instance
    team.save()
