from django.urls import path

from . import views

app_name = "projects"
urlpatterns = [
    path("", views.ProjectList.as_view(), name="list"),
    path("new", views.ProjectCreate.as_view(), name="create"),
    path("<int:pk>", views.ProjectDetail.as_view(), name="detail"),
    path("<int:pk>/update", views.ProjectUpdate.as_view(), name="update"),
    path("<int:pk>/delete", views.ProjectDelete.as_view(), name="delete"),
]
