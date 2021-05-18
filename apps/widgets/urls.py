from django.urls import include, path
from django.views.decorators.cache import cache_control

from . import views

app_name = "widgets"
urlpatterns = [
    path("", views.WidgetList.as_view(), name="list"),
    path("new", views.WidgetCreate.as_view(), name="create"),
    path("<int:pk>", views.WidgetDetail.as_view(), name="detail"),
    path("<int:pk>/update", views.WidgetUpdate.as_view(), name="update"),
    path("<int:pk>/delete", views.WidgetDelete.as_view(), name="delete"),
    path("<int:pk>/config", views.WidgetConfig.as_view(), name="config"),
    # No cache header tells browser to always re-validate the resource
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching#controlling_caching
    # https://web.dev/http-cache/#flowchart
    path(
        "<int:pk>/output",
        cache_control(no_cache=True)(
            views.widget_output_condition(views.WidgetOutput.as_view())
        ),
        name="output",
    ),
]
