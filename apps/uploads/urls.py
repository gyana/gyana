from apps.projects.access import login_and_project_required
from django.urls import path

from . import rest, views

app_name = "integrations"
urlpatterns = [
    path("file/<str:session_key>/generate-signed-url", rest.generate_signed_url),
    path("file/<str:session_key>/start-sync", rest.start_sync),
    path(
        "file/<str:session_key>/upload-complete",
        rest.upload_complete,
        name="upload_complete",
    ),
]

project_urlpatterns = (
    [
        path(
            "upload",
            login_and_project_required(views.IntegrationUpload.as_view()),
            name="upload",
        ),
    ],
    "project_uploads",
)
