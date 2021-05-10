from django.urls import include, path

from . import views

app_name = "projects"
urlpatterns = [
    path("", views.ProjectList.as_view(), name="list"),
    path("new", views.ProjectCreate.as_view(), name="create"),
    path("<int:pk>", views.ProjectDetail.as_view(), name="detail"),
    path("<int:pk>/update", views.ProjectUpdate.as_view(), name="update"),
    path("<int:pk>/delete", views.ProjectDelete.as_view(), name="delete"),
    path("<int:project_id>/datasets/", include("apps.datasets.urls.projects")),
    path("<int:project_id>/connectors/", include("apps.connectors.urls.projects")),
    path("<int:project_id>/dataflows/", include("apps.dataflows.urls.projects")),
    path("<int:project_id>/dashboards/", include("apps.dashboards.urls.projects")),
]
