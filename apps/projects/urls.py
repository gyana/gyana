from django.urls import include, path

from . import views

app_name = "projects"
urlpatterns = [
    path("<int:pk>", views.ProjectDetail.as_view(), name="detail"),
    path("<int:pk>/update", views.ProjectUpdate.as_view(), name="update"),
    path("<int:pk>/delete", views.ProjectDelete.as_view(), name="delete"),
    path("<int:pk>/settings/", views.ProjectSettings.as_view(), name="settings"),
]

team_urlpatterns = (
    [
        path("new", views.ProjectCreate.as_view(), name="create"),
    ],
    "team_projects",
)
