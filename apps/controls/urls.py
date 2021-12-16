from django.contrib.auth.decorators import login_required
from django.urls import path
from rest_framework import routers

from . import frames, rest, views
from .access import (
    control_of_public,
    login_and_control_required,
    login_and_control_widget_required,
)

app_name = "controls"

router = routers.DefaultRouter()
router.register("api", rest.ControlWidgetPartialUpdate, basename="Control")

dashboard_urlpatterns = (
    [
        # Maybe we should move the urls to be under a dashboard url?
        path(
            "new",
            login_required(views.ControlWidgetCreate.as_view()),
            name="create",
        ),
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
            login_and_control_widget_required(views.ControlWidgetDelete.as_view()),
            name="delete",
        ),
    ],
    "dashboard_controls",
)

urlpatterns = router.urls
