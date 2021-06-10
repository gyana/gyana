from django.urls import include, path

from .. import views

app_name = "dashboards"
urlpatterns = [
    path("", views.DashboardList.as_view(), name="list"),
    path("new", views.DashboardCreate.as_view(), name="create"),
    path("<int:pk>", views.DashboardDetail.as_view(), name="detail"),
    path("<int:pk>/delete", views.DashboardDelete.as_view(), name="delete"),
    path("<int:dashboard_id>/widgets/", include("apps.widgets.urls.dashboards")),
]
