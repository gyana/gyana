from apps.teams.access import login_and_team_required
from django.urls import path

from . import views
from .access import login_and_project_required

app_name = "projects"
urlpatterns = [
    path(
        "<hashid:pk>",
        login_and_project_required(views.ProjectDetail.as_view()),
        name="detail",
    ),
    path(
        "<hashid:pk>/update",
        login_and_project_required(views.ProjectUpdate.as_view()),
        name="update",
    ),
    path(
        "<hashid:pk>/delete",
        login_and_project_required(views.ProjectDelete.as_view()),
        name="delete",
    ),
    path(
        "<hashid:pk>/settings/",
        login_and_project_required(views.ProjectSettings.as_view()),
        name="settings",
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
