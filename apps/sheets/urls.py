from django.urls import path
from rest_framework import routers

from apps.projects.access import login_and_project_enabled_required

from . import frames, rest, views
from .access import login_and_sheet_required

app_name = "sheets"
urlpatterns = [
    path(
        "<hashid:pk>/status",
        login_and_sheet_required(frames.SheetStatus.as_view()),
        name="status",
    ),
]

router = routers.DefaultRouter()
router.register("api/sheets", rest.SheetViewSet, basename="Sheet")
urlpatterns += router.urls

integration_urlpatterns = (
    [
        path(
            "new",
            login_and_project_enabled_required(views.SheetCreate.as_view()),
            name="create",
        )
    ],
    "project_integrations_sheets",
)
