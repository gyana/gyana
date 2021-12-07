from django.urls import path

from . import views

app_name = "runs"
urlpatterns = [
    path("", views.RunList.as_view(), name="list"),
    path("new", views.RunCreate.as_view(), name="create"),
    path("<hashid:pk>", views.RunDetail.as_view(), name="detail"),
    path("<hashid:pk>/update", views.RunUpdate.as_view(), name="update"),
    path("<hashid:pk>/delete", views.RunDelete.as_view(), name="delete"),
]
