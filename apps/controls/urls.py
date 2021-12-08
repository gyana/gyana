from django.contrib.auth.decorators import login_required
from django.urls import path

from . import frames
from .access import control_of_public, login_and_control_required

app_name = "controls"

urlpatterns = [
    # Maybe we should move the urls to be under a dashboard url?
    path("new", login_required(frames.ControlCreate.as_view()), name="create"),
    path(
        "<hashid:pk>/update",
        login_and_control_required(frames.ControlUpdate.as_view()),
        name="update",
    ),
    path(
        "<hashid:pk>/update-public",
        control_of_public(frames.ControlPublicUpdate.as_view()),
        name="update-public",
    ),
    path(
        "<hashid:pk>/delete",
        login_and_control_required(frames.ControlDelete.as_view()),
        name="delete",
    ),
]
