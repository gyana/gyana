from django.urls import include, path

from .. import views

app_name = "dashboards"
urlpatterns = [
    path("<int:pk>/sort", views.DashboardSort.as_view(), name="sort"),
]
