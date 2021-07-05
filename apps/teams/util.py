from .models import Team


def get_default_team(request):
    if "team" in request.session:
        try:
            return request.user.teams.get(id=request.session["team"])
        except Team.DoesNotExist:
            # user wasn't member of team from session, or it didn't exist.
            # fall back to default behavior
            del request.session["team"]
            pass
    if request.user.teams.count():
        return request.user.teams.first()
    else:
        return None
