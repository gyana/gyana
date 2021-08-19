from apps.base.access import login_and_permission_to_access
from apps.projects.access import login_and_project_required
from apps.sheets.models import Sheet
from apps.teams.roles import user_can_access_team
from django.shortcuts import get_object_or_404
from django.urls import path

from . import frames, views


def sheet_of_team(user, pk, *args, **kwargs):
    sheet = get_object_or_404(Sheet, pk=pk)
    return user_can_access_team(user, sheet.integration.project.team)


login_and_sheet_required = login_and_permission_to_access(sheet_of_team)

app_name = "sheets"
urlpatterns = [
    path(
        "<hashid:pk>/progress",
        login_and_sheet_required(frames.SheetProgress.as_view()),
        name="progress",
    ),
    path(
        "<hashid:pk>/status",
        login_and_sheet_required(frames.SheetStatus.as_view()),
        name="status",
    ),
    path(
        "<hashid:pk>/update",
        login_and_sheet_required(frames.SheetUpdate.as_view()),
        name="update",
    ),
]

integration_urlpatterns = (
    [
        path(
            "new",
            login_and_project_required(views.SheetCreate.as_view()),
            name="create",
        )
    ],
    "project_integrations_sheets",
)
