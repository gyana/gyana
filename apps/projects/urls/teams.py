from django.urls import include, path

from .. import views

app_name = "projects"
urlpatterns = [
    path("", views.ProjectList.as_view(), name="list"),
    path("new", views.ProjectCreate.as_view(), name="create"),
]
