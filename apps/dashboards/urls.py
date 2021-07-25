from functools import wraps

from apps.projects.access import login_and_project_required
from apps.teams.roles import user_can_access_team
from apps.utils.access import login_and_permission_to_access
from django.shortcuts import get_object_or_404, render
from django.urls import path

from . import views
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


app_name = "dashboards"

urlpatterns = [
    path(
        "<hashid:pk>/sort",
        login_and_dashboard_required(views.DashboardSort.as_view()),
        name="sort",
    ),
    path(
        "<hashid:pk>/duplicate",
        login_and_dashboard_required(views.DashboardDuplicate.as_view()),
        name="duplicate",
    ),
    path(
        "<hashid:pk>",
        login_and_dashboard_required(views.DashboardShare.as_view()),
        name="share",
    ),
    path(
        "<str:shared_id>",
        dashboard_is_public(views.DashboardPublic.as_view()),
        name="public",
    ),
]

project_urlpatterns = (
    [
        path(
            "", login_and_project_required(views.DashboardList.as_view()), name="list"
        ),
        path(
            "new",
            login_and_project_required(views.DashboardCreate.as_view()),
            name="create",
        ),
        path(
            "<hashid:pk>",
            login_and_project_required(views.DashboardDetail.as_view()),
            name="detail",
        ),
        path(
            "<hashid:pk>/delete",
            login_and_project_required(views.DashboardDelete.as_view()),
            name="delete",
        ),
    ],
    "project_dashboards",
)
