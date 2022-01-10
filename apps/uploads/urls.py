from django.urls import path

from apps.projects.access import login_and_project_enabled_required

from . import rest, views

app_name = "uploads"
# TODO: access control and test it
urlpatterns = [
    path("file/generate-signed-url", rest.generate_signed_url),
]

integration_urlpatterns = (
    [
        path(
            "new",
            login_and_project_enabled_required(views.UploadCreate.as_view()),
            name="create",
        )
    ],
    "project_integrations_uploads",
)
