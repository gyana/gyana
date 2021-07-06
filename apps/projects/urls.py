from django.urls import include, path

from . import views

app_name = "projects"
urlpatterns = [
    path("<hashid:pk>", views.ProjectDetail.as_view(), name="detail"),
    path("<hashid:pk>/update", views.ProjectUpdate.as_view(), name="update"),
    path("<hashid:pk>/delete", views.ProjectDelete.as_view(), name="delete"),
    path("<hashid:pk>/settings/", views.ProjectSettings.as_view(), name="settings"),
]

team_urlpatterns = (
    [
        path("new", views.ProjectCreate.as_view(), name="create"),
    ],
    "team_projects",
)
