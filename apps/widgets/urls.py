from apps.projects.access import login_and_project_required
from django.urls import path
from rest_framework import routers

from . import views

app_name = "widgets"
urlpatterns = []

# drf config
router = routers.DefaultRouter()
router.register("api", views.WidgetPartialUpdate, basename="Widget")


urlpatterns += router.urls

dashboard_urlpatterns = (
    [
        path("", login_and_project_required(views.WidgetList.as_view()), name="list"),
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
            "<hashid:pk>/update",
            login_and_project_required(views.WidgetUpdate.as_view()),
            name="update",
        ),
        path(
            "<hashid:pk>/delete",
            login_and_project_required(views.WidgetDelete.as_view()),
            name="delete",
        ),
        # No cache header tells browser to always re-validate the resource
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching#controlling_caching
        # https://web.dev/http-cache/#flowchart
        path(
            "<hashid:pk>/output",
            login_and_project_required(views.WidgetOutput.as_view()),
            name="output",
        ),
    ],
    "dashboard_widgets",
)
