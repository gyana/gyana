from django.urls import path
from rest_framework import routers

from apps.workflows.access import login_and_workflow_required

from . import frames, rest, views
from .access import login_and_node_required

app_name = "nodes"
urlpatterns = [
    # frames
    path(
        "<int:pk>", login_and_node_required(frames.NodeUpdate.as_view()), name="update"
    ),
    path(
        "<int:pk>/grid", login_and_node_required(frames.NodeGrid.as_view()), name="grid"
    ),
    path(
        "<int:pk>/name", login_and_node_required(frames.NodeName.as_view()), name="name"
    ),
    path(
        "<int:pk>/credit_confirmation",
        login_and_node_required(frames.NodeCreditConfirmation.as_view()),
        name="credit-confirmation",
    ),
    path(
        "<int:pk>/formula",
        login_and_node_required(frames.FormulaHelp.as_view()),
        name="formula",
    ),
    path(
        "<int:pk>/function_info",
        login_and_node_required(frames.FunctionInfo.as_view()),
        name="function-info",
    ),
    # This is linked no-where and only used to generate the intercom
    # article article
    path(
        "functions_reference",
        views.FunctionReference.as_view(),
        name="function-reference",
    ),
    # rest
    path(
        "<int:pk>/duplicate",
        login_and_node_required(rest.duplicate_node),
        name="duplicate",
    ),
]


# drf config
router = routers.DefaultRouter()
# Access should be handled on the viewset
router.register("api/nodes", rest.NodeViewSet, basename="Node")
router.register("api/edges", rest.EdgeViewSet, basename="Edge")


urlpatterns += router.urls

workflow_urlpatterns = [
    path(
        "update_positions",
        login_and_workflow_required(rest.update_positions),
        name="update_positions",
    ),
]
