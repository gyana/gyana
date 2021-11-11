import analytics
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from invitations.signals import invite_accepted

from apps.base.analytics import INVITE_ACCEPTED_EVENT, identify_user_group
from apps.users.models import CustomUser

from .models import Invite


def add_user_to_accepted_teams(user: CustomUser):

    teams = user.teams.all()
    for invite in Invite.accepted_by_email(user.email):
        if not invite.team in teams:
            invite.team.members.add(user, through_defaults={"role": invite.role})
            identify_user_group(user, invite.team)

    user.save()

    analytics.track(user.id, INVITE_ACCEPTED_EVENT)


@receiver(invite_accepted)
def add_existing_user_to_team(email, **kwargs):
    user = CustomUser.objects.filter(email=email).first()

    if user:
        add_user_to_accepted_teams(user)


@receiver(user_signed_up)
def add_user_to_team_after_signup(request, user, **kwargs):
    add_user_to_accepted_teams(user)
