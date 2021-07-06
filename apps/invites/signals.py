from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from apps.users.models import CustomUser
from invitations.signals import invite_accepted

from .models import Invite


def add_user_to_accepted_teams(user: CustomUser):

    teams = user.teams.all()
    for invite in Invite.objects.filter(email=user.email, accepted=True).all():
        if not invite.team in teams:
            invite.team.members.add(user, through_defaults={"role": invite.role})

    user.save()


@receiver(invite_accepted)
def add_existing_user_to_team(email, **kwargs):
    user = CustomUser.objects.filter(email=email).first()

    if user:
        add_user_to_accepted_teams(user)


@receiver(user_signed_up)
def add_user_to_team_after_signup(request, user, **kwargs):
    add_user_to_accepted_teams(user)
