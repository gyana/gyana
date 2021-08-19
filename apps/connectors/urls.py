from apps.projects.access import login_and_project_required
from django.conf import settings
from django.urls import path

from . import frames, views

app_name = "connectors"
urlpatterns = [
    path(
        "<hashid:pk>/status",
        frames.ConnectorStatus.as_view(),
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
        path(
            "<hashid:pk>/update",
            login_and_project_required(views.ConnectorUpdate.as_view()),
            name="update",
        ),
        path(
            "<hashid:pk>/load",
            login_and_project_required(views.ConnectorLoad.as_view()),
            name="load",
        ),
    ],
    "project_integrations_connectors",
)
