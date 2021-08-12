from apps.projects.access import login_and_project_required
from django.urls import path

from . import frames, rest, views

app_name = "uploads"
urlpatterns = [
    path("<hashid:pk>/update", frames.UploadUpdate.as_view(), name="update"),
    path("<hashid:pk>/progress", frames.UploadProgress.as_view(), name="progress"),
    path("file/generate-signed-url", rest.generate_signed_url),
]

integration_urlpatterns = (
    [
        path(
            "new",
            login_and_project_required(views.UploadCreate.as_view()),
            name="create",
        ),
    ],
    "project_integrations_uploads",
)
