from functools import wraps

from apps.teams.models import Team
from apps.teams.roles import user_can_access_team
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse


# Inspired by SaaSPegasus
def _get_decorated_function(view_func, permission_test_function):
    """Creates a decorator that tests whether a user is logged in and a has the right permissions to access a view"""

    @wraps(view_func)
    def _inner(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return HttpResponseRedirect(
                "{}?next={}".format(reverse("account_login"), request.path)
            )

        if permission_test_function(user, *args, **kwargs):
            return view_func(request, *args, **kwargs)

        # treat not having access to a team like a 404 to avoid accidentally leaking information
        return render(request, "404.html", status=404)

    return _inner


def login_and_permission_to_access(permission_test_function):
    def decorator(view_func):
        return _get_decorated_function(view_func, permission_test_function)

    return decorator


def login_and_teamid_in_session(view_func):
    """Return a decorator that tests whether a user is logged in and the teamid is in the session."""

    @wraps(view_func)
    def decorator(request, session_key, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return HttpResponseRedirect(
                "{}?next={}".format(reverse("account_login"), request.path)
            )

        team_id = request.session[session_key].get("team_id")
        if team_id is None:
            return render(request, "404.html", status=404)

        team = get_object_or_404(Team, pk=team_id)
        if user_can_access_team(user, team):
            return view_func(request, session_key, *args, **kwargs)

        return render(request, "404.html", status=404)

    return decorator
