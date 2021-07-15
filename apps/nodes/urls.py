from apps.teams.urls import user_is_member
from django.shortcuts import get_object_or_404
from django.urls import path
from lib.decorators import login_and_permission_to_access
from rest_framework import routers

from . import views
from .models import Node


def node_of_team(user, pk, *args, **kwargs):
    node = get_object_or_404(Node, pk=pk)
    return user_is_member(user, node.workflow.project.team)


login_and_node_required = login_and_permission_to_access(node_of_team)

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
    # TODO: How to prevent access
    path("update_positions", views.update_positions, name="update_positions"),
]


# drf config
router = routers.DefaultRouter()
# TODO: How to prevent access? Directly on the viewset?
router.register("api/nodes", views.NodeViewSet, basename="Node")


urlpatterns += router.urls
