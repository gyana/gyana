from apps.projects.access import login_and_project_required
from django.urls import path

from . import rest, views

app_name = "uploads"
urlpatterns = [
    path("file/generate-signed-url", rest.generate_signed_url),
]

integration_urlpatterns = (
    [
        path(
            "new",
            login_and_project_required(views.UploadCreate.as_view()),
            name="create",
        ),
        path(
            "<hashid:pk>/update",
            login_and_project_required(views.UploadUpdate.as_view()),
            name="update",
        ),
        path(
            "<hashid:pk>/load",
            login_and_project_required(views.UploadLoad.as_view()),
            name="load",
        ),
    ],
    "project_integrations_uploads",
)
