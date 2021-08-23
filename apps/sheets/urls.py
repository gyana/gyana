from apps.projects.access import login_and_project_required
from django.urls import path

from . import frames, views
from .access import login_and_sheet_required

app_name = "sheets"
urlpatterns = [
    path(
        "<hashid:pk>/status",
        login_and_sheet_required(frames.SheetStatus.as_view()),
        name="status",
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
