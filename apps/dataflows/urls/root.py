from django.urls import path
from rest_framework import routers

from .. import views

app_name = "dataflows"
urlpatterns = [
    path("<int:pk>/run", views.DataflowRun.as_view(), name="run"),
    path("<int:dataflow_id>/nodes/<int:pk>", views.NodeUpdate.as_view(), name="node"),
    path(
        "<int:dataflow_id>/nodes/<int:pk>/grid", views.NodeGrid.as_view(), name="grid"
    ),
]


# drf config
router = routers.DefaultRouter()
router.register("api/nodes", views.NodeViewSet, basename="Node")

urlpatterns += router.urls
