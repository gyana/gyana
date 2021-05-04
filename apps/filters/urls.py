from django.urls import path

from . import views

app_name = "filters"
urlpatterns = [
    path("", views.FilterList.as_view(), name="list"),
    path("new", views.FilterCreate.as_view(), name="create"),
    path("<int:pk>", views.FilterDetail.as_view(), name="detail"),
    path("<int:pk>/update", views.FilterUpdate.as_view(), name="update"),
    path("<int:pk>/delete", views.FilterDelete.as_view(), name="delete"),
]
