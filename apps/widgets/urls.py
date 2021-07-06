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
        path("", views.WidgetList.as_view(), name="list"),
        path("new", views.WidgetCreate.as_view(), name="create"),
        path("<int:pk>", views.WidgetDetail.as_view(), name="detail"),
        path("<int:pk>/update", views.WidgetUpdate.as_view(), name="update"),
        path("<int:pk>/delete", views.WidgetDelete.as_view(), name="delete"),
        # No cache header tells browser to always re-validate the resource
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching#controlling_caching
        # https://web.dev/http-cache/#flowchart
        path(
            "<int:pk>/output",
            views.WidgetOutput.as_view(),
            name="output",
        ),
    ],
    "dashboard_widgets",
)
