from functools import wraps

from apps.base.access import login_and_permission_to_access
from apps.projects.access import user_can_access_project
from dateutil.parser import isoparse
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Dashboard


def dashboard_of_team(user, pk, *args, **kwargs):
    dashboard = get_object_or_404(Dashboard, pk=pk)
    return user_can_access_project(user, dashboard.project)


login_and_dashboard_required = login_and_permission_to_access(dashboard_of_team)


def can_access_password_protected_dashboard(request, dashboard) -> bool:
    auth = request.session.get(str(dashboard.shared_id))

    return (
        auth
        and dashboard.password_set < isoparse(auth["logged_in"])
        and auth["auth_success"]
    )


def dashboard_is_public(view_func):
    """Returns a decorator that checks whether a dashboard is public or password-protected."""

    @wraps(view_func)
    def decorator(request, *args, **kwargs):
        dashboard = Dashboard.objects.get(shared_id=kwargs["shared_id"])

        if dashboard and dashboard.shared_status == Dashboard.SharedStatus.PUBLIC:
            kwargs["dashboard"] = dashboard
            return view_func(request, *args, **kwargs)

        if (
            dashboard
            and dashboard.shared_status == Dashboard.SharedStatus.PASSWORD_PROTECTED
        ):

            if can_access_password_protected_dashboard(request, dashboard):
                kwargs["dashboard"] = dashboard
                return view_func(request, *args, **kwargs)

            return render(
                request, "dashboards/login.html", context={"object": dashboard}
            )

        return render(request, "404.html", status=404)

    return decorator


def dashboard_is_password_protected(view_func):
    """Returns a decorator that checks whether a dashboard is password-protected."""

    @wraps(view_func)
    def decorator(request, *args, **kwargs):
        dashboard = Dashboard.objects.get(pk=kwargs["pk"])
        if (
            dashboard
            and dashboard.shared_status == Dashboard.SharedStatus.PASSWORD_PROTECTED
        ):
            kwargs["dashboard"] = dashboard
            return view_func(request, *args, **kwargs)
        return render(request, "404.html", status=404)

    return decorator


def dashboard_is_in_template(view_func):
    """Returns a decorator that checks whether a dashboard is in a template."""

    @wraps(view_func)
    def decorator(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return HttpResponseRedirect(
                "{}?next={}".format(reverse("account_login"), request.path)
            )
        dashboard = Dashboard.objects.get(pk=kwargs["pk"])
        if dashboard.project.is_template:
            return view_func(request, *args, **kwargs)
        return render(request, "404.html", status=404)

    return decorator
