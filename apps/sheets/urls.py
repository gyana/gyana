from django.urls import path

from . import frames, views

app_name = "sheets"
urlpatterns = [
    path("<hashid:pk>/status", frames.SheetStatus.as_view(), name="status"),
]

integration_urlpatterns = (
    [path("new", views.SheetCreate.as_view(), name="create")],
    "project_integrations_sheets",
)
