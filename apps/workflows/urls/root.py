from django.urls import path
from rest_framework import routers

from .. import views

app_name = "workflows"
urlpatterns = [
    path("<int:workflow_id>/nodes/<int:pk>", views.NodeUpdate.as_view(), name="node"),
    path(
        "<int:workflow_id>/nodes/<int:pk>/grid", views.NodeGrid.as_view(), name="grid"
    ),
    path("<int:pk>/run_workflow", views.workflow_run, name="run_workflow"),
    path("<int:pk>/out_of_date", views.worflow_out_of_date, name="worflow_out_of_date"),
    path("<int:pk>/last_run", views.WorkflowLastRun.as_view(), name="last_run"),
]


# drf config
router = routers.DefaultRouter()
router.register("api/nodes", views.NodeViewSet, basename="Node")


urlpatterns += router.urls
