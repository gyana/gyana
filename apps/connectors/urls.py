from django.conf import settings
from django.urls import path
from rest_framework import routers

from apps.projects.access import (
    login_and_project_enabled_required,
    login_and_project_required,
)

from . import frames, rest, views
from .access import login_and_connector_required

app_name = "connectors"
urlpatterns = [
    path(
        "<hashid:pk>/icon",
        login_and_connector_required(frames.ConnectorIcon.as_view()),
        name="icon",
    ),
    path(
        "<hashid:pk>/status",
        login_and_connector_required(frames.ConnectorStatus.as_view()),
        name="status",
    ),
]

if settings.DEBUG:
    urlpatterns += [
        path("mock", views.ConnectorMock.as_view(), name="mock"),
    ]

router = routers.DefaultRouter()
router.register("api/connectors", rest.ConnectorViewSet, basename="Connector")
urlpatterns += router.urls

integration_urlpatterns = (
    [
        path(
            "new",
            login_and_project_enabled_required(views.ConnectorCreate.as_view()),
            name="create",
        ),
        path(
            "<hashid:pk>/authorize",
            login_and_project_required(views.ConnectorAuthorize.as_view()),
            name="authorize",
        ),
    ],
    "project_integrations_connectors",
)
