from django.urls import path
from rest_framework import routers

from . import views

app_name = "nodes"
urlpatterns = [
    path("<int:pk>", views.NodeUpdate.as_view(), name="update"),
    path("<int:pk>/grid", views.NodeGrid.as_view(), name="grid"),
    path("<int:pk>/duplicate", views.duplicate_node, name="duplicate"),
    path("<int:pk>/name", views.NodeName.as_view(), name="name"),
    path("update_positions", views.update_positions, name="update_positions"),
]


# drf config
router = routers.DefaultRouter()
router.register("api/nodes", views.NodeViewSet, basename="Node")


urlpatterns += router.urls
