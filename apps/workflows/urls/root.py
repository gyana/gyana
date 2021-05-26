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
]


# drf config
router = routers.DefaultRouter()
router.register("api/nodes", views.NodeViewSet, basename="Node")


urlpatterns += router.urls
