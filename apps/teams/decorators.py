from functools import wraps

from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from .roles import user_can_access_team, user_can_administer_team
from .models import Team



def login_and_team_required(view_func):
    return _get_decorated_function(view_func, user_can_access_team)


def team_admin_required(view_func):
    return _get_decorated_function(view_func, user_can_administer_team)


def _get_decorated_function(view_func, permission_test_function):
    @wraps(view_func)
    def _inner(request, team_slug, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return HttpResponseRedirect('{}?next={}'.format(reverse('account_login'), request.path))
        else:
            team = get_object_or_404(Team, slug=team_slug)
            if permission_test_function(user, team):
                request.team = team
                request.session['team'] = team.id  # set in session for other views to access
                return view_func(request, team_slug, *args, **kwargs)
            else:
                # treat not having access to a team like a 404 to avoid accidentally leaking information
                return render(request, '404.html', status=404)

    return _inner
