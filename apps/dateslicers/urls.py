from django.urls import path

from . import views

app_name = "dateslicers"
urlpatterns = [
    path("new", views.DateSlicerCreate.as_view(), name="create"),
    path("<hashid:pk>/update", views.DateSlicerUpdate.as_view(), name="update"),
    path("<hashid:pk>/delete", views.DateSlicerDelete.as_view(), name="delete"),
]
