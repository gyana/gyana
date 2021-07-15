from apps.teams.access import login_and_team_required
from apps.teams.roles import user_can_access_team
from django.shortcuts import get_object_or_404
from django.urls import path
from lib.decorators import login_and_permission_to_access

from . import views
from .models import Project


def project_of_team(user, pk, *args, **kwargs):
    project = get_object_or_404(Project, pk=pk)
    return user_can_access_team(user, project.team)


login_and_project_required = login_and_permission_to_access(project_of_team)


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
