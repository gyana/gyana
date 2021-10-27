from apps.base.access import login_and_permission_to_access
from apps.teams.roles import user_can_access_team
from django.shortcuts import get_object_or_404

from .models import Project


def project_of_team(user, project_id, *args, **kwargs):
    project = get_object_or_404(Project, pk=project_id)
    return user_can_access_project(user, project)


def project_of_enabled_team(user, project_id, *args, **kwargs):
    project = get_object_or_404(Project, pk=project_id)
    return user_can_access_project(user, project) and project.team.enabled


def user_can_access_project(user, project):
    if project.team.deleted:
        return False
    if project.access == Project.Access.EVERYONE:
        return user_can_access_team(user, project.team)
    return project.members.filter(id=user.id).exists()


login_and_project_required = login_and_permission_to_access(project_of_team)
login_and_project_enabled_required = login_and_permission_to_access(
    project_of_enabled_team
)
