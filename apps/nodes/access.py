from django.shortcuts import get_object_or_404

from apps.base.access import login_and_permission_to_access
from apps.projects.access import user_can_access_project

from .models import Node


def node_of_team(user, pk, *args, **kwargs):
    node = get_object_or_404(Node, pk=pk)
    return user_can_access_project(user, node.workflow.project)


login_and_node_required = login_and_permission_to_access(node_of_team)
