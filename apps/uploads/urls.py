from apps.base.access import login_and_permission_to_access
from apps.projects.access import login_and_project_required
from apps.teams.roles import user_can_access_team
from apps.uploads.models import Upload
from django.shortcuts import get_object_or_404
from django.urls import path

from . import rest, views


def upload_of_team(user, pk, *args, **kwargs):
    upload = get_object_or_404(Upload, pk=pk)
    return user_can_access_team(user, upload.integration.project.team)


login_and_upload_required = login_and_permission_to_access(upload_of_team)

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
        )
    ],
    "project_integrations_uploads",
)
