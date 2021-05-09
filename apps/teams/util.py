from .models import Team
from apps.utils.slug import get_next_unique_slug


def get_next_unique_team_slug(team_name):
    """
    Gets the next unique slug based on the name. Appends -1, -2, etc. until it finds
    a unique value.
    :param team_name:
    :return:
    """
    return get_next_unique_slug(Team, team_name, 'slug')


def get_default_team(request):
    if 'team' in request.session:
        try:
            return request.user.teams.get(id=request.session['team'])
        except Team.DoesNotExist:
            # user wasn't member of team from session, or it didn't exist.
            # fall back to default behavior
            del request.session['team']
            pass
    if request.user.teams.count():
        return request.user.teams.first()
    else:
        return None
