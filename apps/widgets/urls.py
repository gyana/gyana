from django.urls import path
from django.views.decorators.cache import cache_control
from rest_framework import routers

from apps.projects.access import login_and_project_required

from . import cache, frames, rest, views
from .access import (
    login_and_project_required_or_public_or_in_template,
    login_and_widget_required,
)

app_name = "widgets"
urlpatterns = [
    path(
        "<int:pk>/name",
        login_and_widget_required(frames.WidgetName.as_view()),
        name="name",
    )
]

# drf config
router = routers.DefaultRouter()
router.register("api", rest.WidgetPartialUpdate, basename="Widget")


urlpatterns += router.urls

dashboard_urlpatterns = (
    [
        # views
        path(
            "new",
            login_and_project_required(views.WidgetCreate.as_view()),
            name="create",
        ),
        path(
            "<hashid:pk>",
            login_and_project_required(views.WidgetDetail.as_view()),
            name="detail",
        ),
        path(
            "<hashid:pk>/delete",
            login_and_project_required(views.WidgetDelete.as_view()),
            name="delete",
        ),
        # frames
        path(
            "<hashid:pk>/update",
            login_and_project_required(frames.WidgetUpdate.as_view()),
            name="update",
        ),
        path(
            "<hashid:pk>/update-style",
            login_and_project_required(frames.WidgetStyle.as_view()),
            name="update-style",
        ),
        path(
            "<hashid:pk>/input",
            login_and_project_required(frames.WidgetInput.as_view()),
            name="input",
        ),
        path(
            "<hashid:pk>/output",
            cache.widget_output(
                login_and_project_required_or_public_or_in_template(
                    frames.WidgetOutput.as_view()
                )
            ),
            name="output",
        ),
    ],
    "dashboard_widgets",
)
