from django.urls import path

from .. import views

app_name = "workflows"
urlpatterns = [
    path("", views.WorkflowList.as_view(), name="list"),
    path("new", views.WorkflowCreate.as_view(), name="create"),
    path("<int:pk>", views.WorkflowDetail.as_view(), name="detail"),
    path("<int:pk>/update", views.WorkflowUpdate.as_view(), name="update"),
    path("<int:pk>/delete", views.WorkflowDelete.as_view(), name="delete"),
    # path(
    #     "<int:workflow_id>/nodes/<int:pk>/details",
    #     views.node_details,
    #     name="node-detail",
    # ),
]
