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


# These signals run after internal djpaddle signals. The subsription_id and
# subscription_plan_id signals are removed by djpaddle, so we don't know what the
# plan is.


@receiver(subscription_created)
def track_subscription_created(sender, payload, *args, **kwargs):
    analytics.track(payload["user_id"], SUBSCRIPTION_CREATED_EVENT)


@receiver(subscription_updated)
def track_subscription_updated(sender, payload, *args, **kwargs):
    analytics.track(payload["user_id"], SUBSCRIPTION_UPDATED_EVENT)


@receiver(subscription_cancelled)
def track_subscription_cancelled(sender, payload, *args, **kwargs):
    analytics.track(payload["user_id"], SUBSCRIPTION_CANCELLED_EVENT)
