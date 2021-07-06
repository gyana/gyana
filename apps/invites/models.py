from unittest import mock

from django.db import models

from apps.teams import roles
from apps.teams.models import Team
from invitations.models import Invitation


class Invite(Invitation):

    # invitation = models.OneToOneField(Invitation, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="invitations")
    role = models.CharField(
        max_length=100, choices=roles.ROLE_CHOICES, default=roles.ROLE_MEMBER
    )
