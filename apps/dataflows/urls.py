from django.urls import path
from rest_framework import routers

from . import views

app_name = "dataflows"
urlpatterns = [
    path("", views.DataflowList.as_view(), name="list"),
    path("new", views.DataflowCreate.as_view(), name="create"),
    path("<int:pk>", views.DataflowDetail.as_view(), name="detail"),
    path("<int:pk>/update", views.DataflowUpdate.as_view(), name="update"),
    path("<int:pk>/delete", views.DataflowDelete.as_view(), name="delete"),
    path("<int:dataflow_id>/nodes/<int:pk>", views.NodeUpdate.as_view(), name="node"),
]


# drf config
router = routers.DefaultRouter()
router.register("api/nodes", views.NodeViewSet, basename="Node")

urlpatterns += router.urls
