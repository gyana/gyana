from django.conf import settings
from django.urls import path
from django.views.defaults import page_not_found

from apps.projects.access import (
    login_and_project_enabled_required,
    login_and_project_required,
)

from . import frames, views
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
    path(
        "<hashid:pk>/pause",
        login_and_connector_required(frames.ConnectorPause.as_view()),
        name="pause",
    ),
]

if settings.DEBUG:
    urlpatterns += [
        path("mock", views.ConnectorMock.as_view(), name="mock"),
    ]


integration_urlpatterns = (
    [
        path("new", page_not_found, {"exception": Exception()}),
        # path(
        #     "new",
        #     login_and_project_enabled_required(views.ConnectorCreate.as_view()),
        #     name="create",
        # ),
        path(
            "<hashid:pk>/authorize",
            login_and_project_required(views.ConnectorAuthorize.as_view()),
            name="authorize",
        ),
    ],
    "project_integrations_connectors",
)
