from functools import wraps

from apps.dashboards.models import Dashboard
from apps.teams.roles import user_can_access_team
from apps.widgets.models import Widget
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse


def login_and_project_required_or_public_or_in_template(view_func):
    @wraps(view_func)
    def decorator(request, *args, **kwargs):
        widget = Widget.objects.get(pk=kwargs["pk"])
        if widget.dashboard.shared_status == Dashboard.SharedStatus.PUBLIC:
            return view_func(request, *args, **kwargs)
        user = request.user
        if not user.is_authenticated:
            return HttpResponseRedirect(
                "{}?next={}".format(reverse("account_login"), request.path)
            )
        if widget.dashboard.project.is_template:
            return view_func(request, *args, **kwargs)
        team = widget.dashboard.project.team
        if user_can_access_team(user, team):
            return view_func(request, *args, **kwargs)

        return render(request, "404.html", status=404)

    return decorator
