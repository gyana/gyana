from apps.teams.roles import user_can_access_team
from django.shortcuts import get_object_or_404
from lib.decorators import login_and_permission_to_access

from .models import Project


def project_of_team(user, project_id, *args, **kwargs):
    project = get_object_or_404(Project, pk=project_id)
    return user_can_access_team(user, project.team)


login_and_project_required = login_and_permission_to_access(project_of_team)
