import datetime

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.urls import reverse
from django.utils import timezone
from invitations.adapters import get_invitations_adapter
from invitations.base_invitation import AbstractBaseInvitation

from apps.teams import roles
from apps.teams.models import Team

# Modified invitation model for teams with roles
# https://github.com/bee-keeper/django-invitations/blob/master/invitations/models.py


class Invite(AbstractBaseInvitation):

    email = models.EmailField()

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="invitations")
    role = models.CharField(
        max_length=100, choices=roles.ROLE_CHOICES, default=roles.ROLE_MEMBER
    )

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    def key_expired(self):
        expiration_date = self.sent + datetime.timedelta(
            days=settings.INVITATIONS_INVITATION_EXPIRY
        )
        return expiration_date <= timezone.now()

    def send_invitation(self, request, **kwargs):
        current_site = kwargs.pop("site", Site.objects.get_current())
        invite_url = reverse("invitations:accept-invite", args=[self.key])
        invite_url = request.build_absolute_uri(invite_url)
        ctx = kwargs
        ctx.update(
            {
                "invite_url": invite_url,
                "site_name": current_site.name,
                "email": self.email,
                "key": self.key,
                "inviter": self.inviter,
            }
        )

        email_template = "invitations/email/email_invite"

        get_invitations_adapter().send_mail(email_template, self.email, ctx)
        self.sent = timezone.now()
        self.save()

    @property
    def expired(self):
        return self.key_expired()

    def get_absolute_url(self):
        return reverse("team_invites:update", args=(self.team.id, self.id))

    class Meta:
        unique_together = ("team", "email")
        ordering = ("-created",)

    def __str__(self):
        return "Invite: {0}".format(self.email)
