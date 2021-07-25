from apps.teams.roles import user_can_access_team
from apps.utils.access import login_and_permission_to_access
from apps.workflows.models import Workflow
from django.shortcuts import get_object_or_404
from django.urls import path
from rest_framework import routers

from . import views
from .models import Node


def node_of_team(user, pk, *args, **kwargs):
    node = get_object_or_404(Node, pk=pk)
    return user_can_access_team(user, node.workflow.project.team)


def workflow_of_team(user, workflow_id, *args, **kwargs):
    workflow = get_object_or_404(Workflow, pk=workflow_id)
    return user_can_access_team(user, workflow.project.team)


login_and_node_required = login_and_permission_to_access(node_of_team)

login_and_workflow_required = login_and_permission_to_access(workflow_of_team)

app_name = "nodes"
urlpatterns = [
    path(
        "<int:pk>", login_and_node_required(views.NodeUpdate.as_view()), name="update"
    ),
    path(
        "<int:pk>/grid", login_and_node_required(views.NodeGrid.as_view()), name="grid"
    ),
    path(
        "<int:pk>/duplicate",
        login_and_node_required(views.duplicate_node),
        name="duplicate",
    ),
    path(
        "<int:pk>/name", login_and_node_required(views.NodeName.as_view()), name="name"
    ),
]


# drf config
router = routers.DefaultRouter()
# Access should be handled on the viewset
router.register("api/nodes", views.NodeViewSet, basename="Node")


urlpatterns += router.urls

workflow_urlpatterns = [
    path(
        "update_positions",
        login_and_workflow_required(views.update_positions),
        name="update_positions",
    ),
]
