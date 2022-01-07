from django.shortcuts import get_object_or_404

from apps.base.access import login_and_permission_to_access
from apps.nodes.models import Node
from apps.projects.access import user_can_access_project
from apps.tables.models import Table


def node_of_project(user, *args, **kwargs):
    node = get_object_or_404(Node, pk=kwargs["parent_id"])
    return user_can_access_project(user, node.workflow.project)


def integration_table_of_project(user, *args, **kwargs):
    table = get_object_or_404(Table, pk=kwargs["parent_id"])
    return user_can_access_project(user, table.integration.project)


login_and_node_required = login_and_permission_to_access(node_of_project)
login_and_table_required = login_and_permission_to_access(integration_table_of_project)
