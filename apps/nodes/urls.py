from django.urls import path
from rest_framework import routers

from . import views

app_name = "nodes"
urlpatterns = [
    path("<hashid:pk>/duplicate_node", views.duplicate_node, name="duplicate_node"),
    path("<hashid:pk>/node_name", views.NodeName.as_view(), name="node_name"),
    path("update_positions", views.update_positions, name="update_positions"),
]


# drf config
router = routers.DefaultRouter()
router.register("api/nodes", views.NodeViewSet, basename="Node")


urlpatterns += router.urls

workflow_urlpatterns = [
    path("<hashid:pk>", views.NodeUpdate.as_view(), name="node"),
    path("<hashid:pk>/grid", views.NodeGrid.as_view(), name="grid"),
]
