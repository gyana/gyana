from apps.projects.access import login_and_project_required
from apps.teams.roles import user_can_access_team
from django.shortcuts import get_object_or_404
from django.urls import path
from lib.decorators import login_and_permission_to_access

from . import views
from .models import Dashboard


def dashboard_of_team(user, pk, *args, **kwargs):
    dashboard = get_object_or_404(Dashboard, pk=pk)
    return user_can_access_team(user, dashboard.project.team)


login_and_dashboard_required = login_and_permission_to_access(dashboard_of_team)

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
