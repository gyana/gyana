from django.shortcuts import get_object_or_404

from apps.base.access import login_and_permission_to_access
from apps.projects.access import user_can_access_project

from .models import Workflow


def workflow_of_team(user, pk, *args, **kwargs):
    workflow = get_object_or_404(Workflow, pk=pk)
    return user_can_access_project(user, workflow.project)


login_and_workflow_required = login_and_permission_to_access(workflow_of_team)
