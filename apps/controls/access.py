from functools import wraps

from django.shortcuts import get_object_or_404, render

from apps.controls.models import Control
from apps.dashboards.access import can_access_password_protected_dashboard
from apps.dashboards.models import Dashboard


def control_of_public(view_func):
    """Returns a decorator that checks whether a control belongs
    to a public or password protected dashboard."""

    @wraps(view_func)
    def decorator(request, *args, **kwargs):

        control = get_object_or_404(Control, pk=kwargs["pk"])
        dashboard = control.page.dashboard

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
