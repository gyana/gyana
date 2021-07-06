from django.urls import path
from rest_framework import routers

from . import views

app_name = "workflows"
urlpatterns = [
    path(
        "<hashid:workflow_id>/nodes/<hashid:pk>",
        views.NodeUpdate.as_view(),
        name="node",
    ),
    path(
        "<hashid:workflow_id>/nodes/<hashid:pk>/grid",
        views.NodeGrid.as_view(),
        name="grid",
    ),
    path("<hashid:pk>/run_workflow", views.workflow_run, name="run_workflow"),
    path(
        "<hashid:pk>/out_of_date", views.worflow_out_of_date, name="worflow_out_of_date"
    ),
    path("<hashid:pk>/last_run", views.WorkflowLastRun.as_view(), name="last_run"),
    path("<hashid:pk>/duplicate_node", views.duplicate_node, name="duplicate_node"),
    path("<hashid:pk>/node_name", views.NodeName.as_view(), name="node_name"),
]

# drf config
router = routers.DefaultRouter()
router.register("api/nodes", views.NodeViewSet, basename="Node")


urlpatterns += router.urls

project_urlpatterns = (
    [
        path("", views.WorkflowList.as_view(), name="list"),
        path("new", views.WorkflowCreate.as_view(), name="create"),
        path("<hashid:pk>", views.WorkflowDetail.as_view(), name="detail"),
        path("<hashid:pk>/delete", views.WorkflowDelete.as_view(), name="delete"),
    ],
    "project_workflows",
)
