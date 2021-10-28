import json

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch.dispatcher import receiver
from djpaddle.models import Subscription

from .bigquery import delete_team_dataset
from .models import Team


@receiver(post_delete, sender=Team)
def delete_bigquery_dataset(sender, instance, *args, **kwargs):
    if settings.MOCK_REMOTE_OBJECT_DELETION:
        return

    delete_team_dataset(instance)


@receiver(post_save, sender=Subscription)
def paddle_subscription_reciever(sender, instance, created, **kwargs):
    if created:
        team_id = json.loads(instance.passthrough)["team_id"]
        team = Team.objects.filter(pk=team_id).first()

        if team is not None:
            team.subscription = instance
            team.save()
