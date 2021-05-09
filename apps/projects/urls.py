from django.urls import path

from . import views

app_name = "projects"
urlpatterns = [
    path("", views.ProjectList.as_view(), name="list"),
    path("new", views.ProjectCreate.as_view(), name="create"),
    path("<int:pk>", views.ProjectDetail.as_view(), name="detail"),
    path("<int:pk>/update", views.ProjectUpdate.as_view(), name="update"),
    path("<int:pk>/delete", views.ProjectDelete.as_view(), name="delete"),
    path("<int:pk>/connectors", views.ProjectConnectors.as_view(), name="connectors"),
    path("<int:pk>/datasets", views.ProjectDatasets.as_view(), name="datasets"),
    path("<int:pk>/dataflows", views.ProjectDataflows.as_view(), name="dataflows"),
    path("<int:pk>/dashboards", views.ProjectDashboards.as_view(), name="dashboards"),
]
