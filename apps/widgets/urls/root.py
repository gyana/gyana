from django.urls import include, path
from django.views.decorators.cache import cache_control

from .. import views

app_name = "widgets"
urlpatterns = [
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
