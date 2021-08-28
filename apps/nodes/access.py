from apps.base.access import login_and_permission_to_access
from apps.teams.roles import user_can_access_team
from apps.workflows.models import Workflow
from django.shortcuts import get_object_or_404

from .models import Node


def node_of_team(user, pk, *args, **kwargs):
    node = get_object_or_404(Node, pk=pk)
    return user_can_access_team(user, node.workflow.project.team)


def workflow_of_team(user, workflow_id, *args, **kwargs):
    workflow = get_object_or_404(Workflow, pk=workflow_id)
    return user_can_access_team(user, workflow.project.team)


login_and_node_required = login_and_permission_to_access(node_of_team)

login_and_workflow_required = login_and_permission_to_access(workflow_of_team)
