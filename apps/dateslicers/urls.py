from django.urls import path

from . import frames

app_name = "dateslicers"
urlpatterns = [
    path("new", frames.DateSlicerCreate.as_view(), name="create"),
    path("<hashid:pk>/update", frames.DateSlicerUpdate.as_view(), name="update"),
    path("<hashid:pk>/delete", frames.DateSlicerDelete.as_view(), name="delete"),
]
