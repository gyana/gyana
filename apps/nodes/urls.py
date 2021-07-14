from django.urls import path
from rest_framework import routers

from . import views

app_name = "nodes"
urlpatterns = [
    path("<hashid:pk>", views.NodeUpdate.as_view(), name="update"),
    path("<hashid:pk>/grid", views.NodeGrid.as_view(), name="grid"),
    path("<hashid:pk>/duplicate", views.duplicate_node, name="duplicate"),
    path("<hashid:pk>/name", views.NodeName.as_view(), name="name"),
    path("update_positions", views.update_positions, name="update_positions"),
]


# drf config
router = routers.DefaultRouter()
router.register("api/nodes", views.NodeViewSet, basename="Node")


urlpatterns += router.urls
