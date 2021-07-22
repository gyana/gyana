from apps.teams.models import Team
from apps.teams.roles import user_can_access_team
from django.shortcuts import get_object_or_404
from lib.decorators import login_and_permission_to_access


def user_is_member(user, team_id, *args, **kwargs):
    team = get_object_or_404(Team, pk=team_id)
    return user_can_access_team(user, team)


login_and_team_required = login_and_permission_to_access(user_is_member)
