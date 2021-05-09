
ROLE_ADMIN = 'admin'
ROLE_MEMBER = 'member'

ROLE_CHOICES = (
    # customize roles here
    (ROLE_ADMIN, 'Administrator'),
    (ROLE_MEMBER, 'Member'),
)


def user_can_access_team(user, team):
    return user.is_superuser or is_member(user, team)


def user_can_administer_team(user, team):
    return user.is_superuser or is_admin(user, team)


def is_member(user, team):
    return team.members.filter(id=user.id).exists()


def is_admin(user, team):
    from .models import Membership
    return Membership.objects.filter(team=team, user=user, role=ROLE_ADMIN).exists()
