from django.urls import path

from .. import views

app_name = "workflows"
urlpatterns = [
    path("", views.WorkflowList.as_view(), name="list"),
    path("new", views.WorkflowCreate.as_view(), name="create"),
    path("<int:pk>", views.WorkflowDetail.as_view(), name="detail"),
    path("<int:pk>/delete", views.WorkflowDelete.as_view(), name="delete"),
]
