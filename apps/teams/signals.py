import json

import analytics
from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch.dispatcher import receiver
from djpaddle.models import Checkout
from djpaddle.signals import (
    subscription_cancelled,
    subscription_created,
    subscription_updated,
)

from apps.base.analytics import (
    SUBSCRIPTION_CANCELLED_EVENT,
    SUBSCRIPTION_CREATED_EVENT,
    SUBSCRIPTION_UPDATED_EVENT,
)

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


@receiver(subscription_created)
def track_subscription_created(sender, payload, *args, **kwargs):
    analytics.track(
        payload["user_id"],
        SUBSCRIPTION_CREATED_EVENT,
        {"plan": payload["subscription_plan_id"]},
    )


@receiver(subscription_updated)
def track_subscription_updated(sender, payload, *args, **kwargs):
    if payload["old_subscription_plan_id"] != payload["subscription_plan_id"]:
        analytics.track(
            payload["user_id"],
            SUBSCRIPTION_UPDATED_EVENT,
            {"plan": payload["subscription_plan_id"]},
        )


@receiver(subscription_cancelled)
def track_subscription_cancelled(sender, payload, *args, **kwargs):
    analytics.track(
        payload["user_id"],
        SUBSCRIPTION_CANCELLED_EVENT,
        {"plan": payload["subscription_plan_id"]},
    )
