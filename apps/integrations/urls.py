from apps.base.access import login_and_teamid_in_session
from apps.projects.access import login_and_project_required
from django.urls import path

from . import frames, rest, views
from .access import login_and_integration_required

app_name = "integrations"
urlpatterns = [
    # frames
    path(
        "<hashid:pk>/grid",
        login_and_integration_required(frames.IntegrationGrid.as_view()),
        name="grid",
    ),
    path(
        "<hashid:pk>/sync",
        login_and_integration_required(frames.IntegrationSync.as_view()),
        name="sync",
    ),
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

project_urlpatterns = (
    [
        # views
        path(
            "", login_and_project_required(views.IntegrationList.as_view()), name="list"
        ),
        path(
            "new",
            login_and_project_required(views.IntegrationNew.as_view()),
            name="new",
        ),
        path(
            "create",
            login_and_project_required(views.IntegrationCreate.as_view()),
            name="create",
        ),
        path(
            "<hashid:pk>",
            login_and_project_required(views.IntegrationDetail.as_view()),
            name="detail",
        ),
        path(
            "<str:session_key>/setup",
            login_and_project_required(views.ConnectorSetup.as_view()),
            name="setup",
        ),
        path(
            "<hashid:pk>/update",
            login_and_project_required(views.IntegrationUpdate.as_view()),
            name="update",
        ),
        path(
            "<hashid:pk>/delete",
            login_and_project_required(views.IntegrationDelete.as_view()),
            name="delete",
        ),
        path(
            "<hashid:pk>/structure",
            login_and_project_required(views.IntegrationStructure.as_view()),
            name="structure",
        ),
        path(
            "<hashid:pk>/data",
            login_and_project_required(views.IntegrationData.as_view()),
            name="data",
        ),
        path(
            "<hashid:pk>/schema",
            login_and_project_required(views.IntegrationSchema.as_view()),
            name="schema",
        ),
        path(
            "<hashid:pk>/settings",
            login_and_project_required(views.IntegrationSettings.as_view()),
            name="settings",
        ),
        path(
            "<hashid:pk>/sheet-verify",
            login_and_project_required(views.IntegrationDetail.as_view()),
            name="sheet-verify",
        ),
        # frames
        path(
            "<hashid:pk>/tables",
            login_and_project_required(frames.IntegrationTablesList.as_view()),
            name="tables",
        ),
    ],
    "project_integrations",
)
