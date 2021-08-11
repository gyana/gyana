from apps.base.access import login_and_teamid_in_session
from apps.projects.access import login_and_project_required
from django.conf import settings
from django.urls import path

from . import frames, rest, views

app_name = "connectors"
urlpatterns = [
    # rest
    # TODO: access control?
    path(
        "<str:session_key>/start-fivetran-integration",
        login_and_teamid_in_session(rest.start_fivetran_integration),
        name="start-fivetran-integration",
    ),
    path(
        "<str:session_key>/finalise-fivetran-integration",
        login_and_teamid_in_session(rest.finalise_fivetran_integration),
        name="finalise-fivetran-integration",
    ),
    path("<hashid:pk>/update", frames.ConnectorUpdate.as_view(), name="update"),
    # path(
    #     "<str:session_key>/setup",
    #     login_and_project_required(views.ConnectorSetup.as_view()),
    #     name="setup",
    # ),
    path(
        "<hashid:pk>/schema",
        login_and_project_required(frames.ConnectorSchema.as_view()),
        name="schema",
    ),
]

if settings.DEBUG:
    urlpatterns += [
        path("mock", views.ConnectorMock.as_view(), name="mock"),
    ]


integration_urlpatterns = (
    [
        # views
        path(
            "new",
            login_and_project_required(views.ConnectorCreate.as_view()),
            name="create",
        ),
    ],
    "project_integrations_connectors",
)
