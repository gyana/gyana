from django.urls import path

from . import frames

app_name = "sheets"
integrations_urlpatterns = (
    [
        path("<hashid:pk>/sync", frames.IntegrationSync.as_view(), name="sync"),
    ],
    "project_integrations_sheets",
)
