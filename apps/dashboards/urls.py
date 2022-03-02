from django.urls import path
from rest_framework import routers

from apps.projects.access import login_and_project_required

from . import frames, rest, views
from .access import (
    dashboard_is_in_template,
    dashboard_is_password_protected,
    dashboard_is_public,
    login_and_dashboard_required,
)

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
    path(
        "<str:shared_id>/login",
        dashboard_is_password_protected(views.DashboardLogin.as_view()),
        name="login",
    ),
    path(
        "<str:shared_id>/logout",
        dashboard_is_password_protected(views.DashboardLogout.as_view()),
        name="logout",
    ),
    # frames
    path(
        "<hashid:pk>/share",
        login_and_dashboard_required(frames.DashboardShare.as_view()),
        name="share",
    ),
    path(
        "<hashid:pk>/preview",
        dashboard_is_in_template(frames.DashboardPreview.as_view()),
        name="preview",
    ),
]

router = routers.DefaultRouter()
router.register("api/dashboards", rest.DashboardViewSet, basename="Dashboard")
urlpatterns += router.urls

project_urlpatterns = (
    [
        path(
            "", login_and_project_required(views.DashboardList.as_view()), name="list"
        ),
        path(
            "overview",
            login_and_project_required(frames.DashboardOverview.as_view()),
            name="overview",
        ),
        path(
            "new",
            login_and_project_required(views.DashboardCreate.as_view()),
            name="create",
        ),
        path(
            "create_from_integration",
            login_and_project_required(views.DashboardCreateFromIntegration.as_view()),
            name="create_from_integration",
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
        path(
            "<hashid:dashboard_id>/pages/new",
            login_and_project_required(views.PageCreate.as_view()),
            name="page-create",
        ),
        path(
            "<hashid:dashboard_id>/pages/<hashid:pk>",
            login_and_project_required(views.PageDelete.as_view()),
            name="page-delete",
        ),
        # Turbo frames
        path(
            "<hashid:pk>/settings",
            login_and_project_required(frames.DashboardSettings.as_view()),
            name="settings",
        ),
        path(
            "<hashid:pk>/history",
            login_and_project_required(frames.DashboardHistory.as_view()),
            name="history",
        ),
    ],
    "project_dashboards",
)
