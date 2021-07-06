from django.urls import include, path

from . import views

app_name = "dashboards"

urlpatterns = [
    path("<hashid:pk>/sort", views.DashboardSort.as_view(), name="sort"),
]

project_urlpatterns = (
    [
        path("", views.DashboardList.as_view(), name="list"),
        path("new", views.DashboardCreate.as_view(), name="create"),
        path("<hashid:pk>", views.DashboardDetail.as_view(), name="detail"),
        path("<hashid:pk>/delete", views.DashboardDelete.as_view(), name="delete"),
    ],
    "project_dashboards",
)
