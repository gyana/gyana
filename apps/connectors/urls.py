from apps.base.access import login_and_permission_to_access
from apps.connectors.models import Connector
from apps.projects.access import login_and_project_required
from apps.teams.roles import user_can_access_team
from django.conf import settings
from django.urls import path
from rest_framework.generics import get_object_or_404

from . import frames, views


def connector_of_team(user, pk, *args, **kwargs):
    connector = get_object_or_404(Connector, pk=pk)
    return user_can_access_team(user, connector.integration.project.team)


login_and_connector_required = login_and_permission_to_access(connector_of_team)

app_name = "connectors"
urlpatterns = [
    path(
        "<hashid:pk>/update",
        login_and_connector_required(frames.ConnectorUpdate.as_view()),
        name="update",
    ),
    path(
        "<hashid:pk>/progress",
        login_and_connector_required(frames.ConnectorProgress.as_view()),
        name="progress",
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


integration_urlpatterns = (
    [
        path(
            "new",
            login_and_project_required(views.ConnectorCreate.as_view()),
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
