from django.contrib.auth.decorators import login_required
from django.urls import path

from . import frames
from .access import dateslicer_of_public, login_and_dateslicer_required

app_name = "dateslicers"

urlpatterns = [
    # Maybe we should move the urls to be under a dashboard url?
    path("new", login_required(frames.DateSlicerCreate.as_view()), name="create"),
    path(
        "<hashid:pk>/update",
        login_and_dateslicer_required(frames.DateSlicerUpdate.as_view()),
        name="update",
    ),
    path(
        "<hashid:pk>/update-public",
        dateslicer_of_public(frames.DateSlicerPublicUpdate.as_view()),
        name="update-public",
    ),
    path(
        "<hashid:pk>/delete",
        login_and_dateslicer_required(frames.DateSlicerDelete.as_view()),
        name="delete",
    ),
]
