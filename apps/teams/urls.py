from django.urls import path

from . import views

app_name = "teams"

urlpatterns = [
    path("new/", views.TeamCreate.as_view(), name="create"),
    path("<int:pk>", views.TeamDetail.as_view(), name="detail"),
    path("<int:pk>/update", views.TeamUpdate.as_view(), name="update"),
    path("<int:pk>/delete", views.TeamDelete.as_view(), name="delete"),
    path("<int:pk>/members", views.TeamMembers.as_view(), name="members"),
]
