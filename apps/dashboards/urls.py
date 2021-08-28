from apps.projects.access import login_and_project_required
from django.urls import path

from . import frames, rest, views
from .access import dashboard_is_public, login_and_dashboard_required

app_name = "dashboards"

urlpatterns = [
    # views
    path(
        "<hashid:pk>/duplicate",
        login_and_dashboard_required(views.DashboardDuplicate.as_view()),
        name="duplicate",
    ),
    path(
        "<str:shared_id>",
        dashboard_is_public(views.DashboardPublic.as_view()),
        name="public",
    ),
    # frames
    path(
        "<hashid:pk>/share",
        login_and_dashboard_required(frames.DashboardShare.as_view()),
        name="share",
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
