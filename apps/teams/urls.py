from django.urls import path

from . import views

app_name = "teams"

urlpatterns = [
    path("new/", views.TeamCreate.as_view(), name="create"),
    path("<hashid:pk>", views.TeamDetail.as_view(), name="detail"),
    path("<hashid:pk>/update", views.TeamUpdate.as_view(), name="update"),
    path("<hashid:pk>/delete", views.TeamDelete.as_view(), name="delete"),
    path("<hashid:pk>/members", views.TeamMembers.as_view(), name="members"),
]
