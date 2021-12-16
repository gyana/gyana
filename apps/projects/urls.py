from django.urls import path

from apps.teams.access import login_and_team_required

from . import frames, rest, views
from .access import login_and_project_required

app_name = "projects"
urlpatterns = [
    path(
        "<hashid:project_id>",
        login_and_project_required(views.ProjectDetail.as_view()),
        name="detail",
    ),
    path(
        "<hashid:project_id>/update",
        login_and_project_required(views.ProjectUpdate.as_view()),
        name="update",
    ),
    path(
        "<hashid:project_id>/delete",
        login_and_project_required(views.ProjectDelete.as_view()),
        name="delete",
    ),
    path(
        "<hashid:project_id>/automate",
        login_and_project_required(views.ProjectAutomate.as_view()),
        name="automate",
    ),
    path(
        "<hashid:project_id>/runs",
        login_and_project_required(frames.ProjectRuns.as_view()),
        name="runs",
    ),
    path(
        "<int:project_id>/run",
        login_and_project_required(rest.project_run),
        name="run",
    ),
]

team_urlpatterns = (
    [
        path(
            "new", login_and_team_required(views.ProjectCreate.as_view()), name="create"
        ),
    ],
    "team_projects",
)
