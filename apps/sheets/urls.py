from django.urls import path

from . import frames, views

app_name = "sheets"
urlpatterns = [
    path("<hashid:pk>/progress", frames.SheetProgress.as_view(), name="progress"),
    path("<hashid:pk>/status", frames.SheetStatus.as_view(), name="status"),
    path("<hashid:pk>/update", frames.SheetUpdate.as_view(), name="update"),
]

integration_urlpatterns = (
    [path("new", views.SheetCreate.as_view(), name="create")],
    "project_integrations_sheets",
)
