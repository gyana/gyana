from apps.integrations.models import Integration
from apps.projects.access import login_and_project_required
from apps.teams.roles import user_can_access_team
from django.shortcuts import get_object_or_404
from django.urls import path
from lib.decorators import login_and_permission_to_access

from . import views


def integration_of_team(user, pk, *args, **kwargs):
    integration = get_object_or_404(Integration, pk=pk)
    return user_can_access_team(user, integration.project.team)


login_and_integration_required = login_and_permission_to_access(integration_of_team)

app_name = "integrations"
urlpatterns = [
    path(
        "<hashid:pk>/grid",
        login_and_integration_required(views.IntegrationGrid.as_view()),
        name="grid",
    ),
    path(
        "<hashid:pk>/sync",
        login_and_integration_required(views.IntegrationSync.as_view()),
        name="sync",
    ),
    path(
        "<hashid:pk>/authorize",
        login_and_integration_required(views.IntegrationAuthorize.as_view()),
        name="authorize",
    ),
    path(
        "<hashid:pk>/authorize-fivetran",
        login_and_integration_required(views.authorize_fivetran),
        name="authorize-fivetran",
    ),
    path(
        "<hashid:pk>/authorize-fivetran-redirect",
        login_and_integration_required(views.authorize_fivetran_redirect),
        name="authorize-fivetran-redirect",
    ),
    path(
        "<hashid:pk>/start-fivetran-integration",
        login_and_integration_required(views.start_fivetran_integration),
        name="start-fivetran-integration",
    ),
    # TODO: access control?
    path("file/<str:session_key>/generate-signed-url", views.generate_signed_url),
    path("file/<str:session_key>/start-sync", views.start_sync),
    path(
        "file/<str:session_key>/upload-complete",
        views.upload_complete,
        name="upload_complete",
    ),
]

project_urlpatterns = (
    [
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
            "upload",
            login_and_project_required(views.IntegrationUpload.as_view()),
            name="upload",
        ),
        path(
            "<hashid:pk>",
            login_and_project_required(views.IntegrationDetail.as_view()),
            name="detail",
        ),
        path(
            "<hashid:pk>/setup",
            login_and_project_required(views.IntegrationSetup.as_view()),
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
            "<hashid:pk>/tables",
            login_and_project_required(views.IntegrationTablesList.as_view()),
            name="tables",
        ),
        path(
            "<hashid:pk>/sheet-verify",
            login_and_project_required(views.IntegrationDetail.as_view()),
            name="sheet-verify",
        ),
    ],
    "project_integrations",
)
