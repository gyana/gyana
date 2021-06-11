from apps.teams.decorators import login_and_team_required
from apps.teams.util import get_default_team
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


def home(request):
    if request.user.is_authenticated:
        if (team := get_default_team(request)) :
            return HttpResponseRedirect(
                reverse("team_projects:list", args=(team.slug,))
            )
        return HttpResponseRedirect(reverse("teams:create_team"))
    return redirect("/accounts/login")


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
