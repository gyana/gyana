from apps.subscriptions.helpers import SubscriptionModelMixin
from apps.utils.models import BaseModel
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from . import roles


class Team(SubscriptionModelMixin, BaseModel):
    """
    A Team, with members.
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    subscription = models.ForeignKey(
        "djstripe.Subscription",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("The team's Stripe Subscription object, if it exists"),
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="teams", through="Membership"
    )

    def __str__(self):
        return self.name


class Membership(BaseModel):
    """
    A user's team membership
    """

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, choices=roles.ROLE_CHOICES)
