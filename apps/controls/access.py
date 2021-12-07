from functools import wraps

from django.shortcuts import get_object_or_404, render

from apps.base.access import login_and_permission_to_access
from apps.controls.models import Control
from apps.dashboards.access import can_access_password_protected_dashboard
from apps.dashboards.models import Dashboard
from apps.projects.access import user_can_access_project


def control_of_team(user, pk, *args, **kwargs):
    control = get_object_or_404(Control, pk=pk)
    project = control.dashboard.project
    return user_can_access_project(user, project)


login_and_control_required = login_and_permission_to_access(control_of_team)


def control_of_public(view_func):
    """Returns a decorator that checks whether a control belongs
    to a public or password protected dashboard."""

    @wraps(view_func)
    def decorator(request, *args, **kwargs):

        control = get_object_or_404(Control, pk=kwargs["pk"])
        dashboard = control.dashboard

        if not dashboard or dashboard.project.team.deleted:
            return render(request, "404.html", status=404)

        if dashboard.shared_status == Dashboard.SharedStatus.PUBLIC:
            return view_func(request, *args, **kwargs)

        if (
            dashboard.shared_status == Dashboard.SharedStatus.PASSWORD_PROTECTED
            and can_access_password_protected_dashboard(request, dashboard)
        ):
            return view_func(request, *args, **kwargs)

        return render(request, "404.html", status=404)

    return decorator
