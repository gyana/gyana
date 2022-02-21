from django.urls import path
from rest_framework import routers

from apps.projects.access import login_and_project_required

from . import frames, rest, views
from .access import control_of_public

app_name = "controls"

router = routers.DefaultRouter()
router.register("api", rest.ControlWidgetPartialUpdate, basename="Control")

dashboard_urlpatterns = (
    [
        # Maybe we should move the urls to be under a dashboard url?
        path(
            "new-widget",
            login_and_project_required(views.ControlWidgetCreate.as_view()),
            name="create-widget",
        ),
        path(
            "<hashid:pk>/update-widget",
            login_and_project_required(frames.ControlUpdate.as_view()),
            name="update-widget",
        ),
        path(
            "<hashid:pk>/update-public",
            control_of_public(frames.ControlPublicUpdate.as_view()),
            name="update-public",
        ),
        path(
            "<hashid:pk>/delete-widget",
            login_and_project_required(views.ControlWidgetDelete.as_view()),
            name="delete-widget",
        ),
    ],
    "dashboard_controls",
)

urlpatterns = router.urls
