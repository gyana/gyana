from functools import wraps

from apps.teams.roles import user_can_access_team
from apps.base.access import login_and_permission_to_access
from django.shortcuts import get_object_or_404, render

from .models import Dashboard


def dashboard_of_team(user, pk, *args, **kwargs):
    dashboard = get_object_or_404(Dashboard, pk=pk)
    return user_can_access_team(user, dashboard.project.team)


login_and_dashboard_required = login_and_permission_to_access(dashboard_of_team)


def dashboard_is_public(view_func):
    """Returns a decorator that checks whether a dashboard is public."""

    @wraps(view_func)
    def decorator(request, *args, **kwargs):
        dashboard = Dashboard.objects.get(shared_id=kwargs["shared_id"])
        if dashboard and dashboard.shared_status == Dashboard.SharedStatus.PUBLIC:
            kwargs["dashboard"] = dashboard
            return view_func(request, *args, **kwargs)
        return render(request, "404.html", status=404)

    return decorator
