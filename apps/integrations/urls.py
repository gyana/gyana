from apps.base.access import login_and_teamid_in_session
from apps.projects.access import login_and_project_required
from django.urls import path

from . import frames, views
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
        "<hashid:pk>/schema",
        login_and_integration_required(frames.IntegrationSchema.as_view()),
        name="schema",
    ),
]

project_urlpatterns = (
    [
        # views
        path(
            "", login_and_project_required(views.IntegrationList.as_view()), name="list"
        ),
        path(
            "pending",
            login_and_project_required(views.IntegrationPending.as_view()),
            name="pending",
        ),
        path(
            "<hashid:pk>/setup",
            login_and_project_required(views.IntegrationSetup.as_view()),
            name="setup",
        ),
        path(
            "<hashid:pk>",
            login_and_project_required(views.IntegrationDetail.as_view()),
            name="detail",
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
            "<hashid:pk>/data",
            login_and_project_required(views.IntegrationData.as_view()),
            name="data",
        ),
        path(
            "<hashid:pk>/settings",
            login_and_project_required(views.IntegrationSettings.as_view()),
            name="settings",
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
