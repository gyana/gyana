from apps.base.access import login_and_permission_to_access
from apps.teams.roles import user_can_access_team
from apps.uploads.models import Upload
from django.shortcuts import get_object_or_404


def upload_of_team(user, pk, *args, **kwargs):
    upload = get_object_or_404(Upload, pk=pk)
    team = upload.integration.project.team
    return not team.deleted and user_can_access_team(user, team)


login_and_upload_required = login_and_permission_to_access(upload_of_team)
