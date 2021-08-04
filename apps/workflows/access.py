from apps.teams.roles import user_can_access_team
from apps.utils.access import login_and_permission_to_access
from django.shortcuts import get_object_or_404

from .models import Workflow


def workflow_of_team(user, pk, *args, **kwargs):
    workflow = get_object_or_404(Workflow, pk=pk)
    return user_can_access_team(user, workflow.project.team)


login_and_workflow_required = login_and_permission_to_access(workflow_of_team)
