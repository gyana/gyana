from apps.base.access import login_and_teamid_in_session
from apps.projects.access import login_and_project_required
from django.urls import path

from . import rest, views

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
]

integration_urlpatterns = (
    [
        # views
        path(
            "<str:session_key>/setup",
            login_and_project_required(views.ConnectorSetup.as_view()),
            name="setup",
        ),
        path(
            "<hashid:pk>/schema",
            login_and_project_required(views.IntegrationSchema.as_view()),
            name="schema",
        ),
    ],
    "project_integrations_connectors",
)
