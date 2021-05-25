from apps.teams.decorators import login_and_team_required
from apps.teams.util import get_default_team
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


def home(request):
    if request.user.is_authenticated:

        team = get_default_team(request)
        if team:
            return HttpResponseRedirect(reverse("projects:list"))
        else:
            messages.info(
                request,
                _(
                    "Teams are enabled but you have no teams. "
                    "Create a team below to access the rest of the dashboard."
                ),
            )
            return HttpResponseRedirect(reverse("teams:manage_teams"))

    else:
        return redirect('/accounts/login')


@login_and_team_required
def team_home(request, team_slug):
    assert request.team.slug == team_slug
    return render(
        request,
        "web/app_home.html",
        context={
            "team": request.team,
            "active_tab": "dashboard",
        },
    )
