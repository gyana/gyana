from django.views.decorators.cache import cache_control
from django.views.decorators.http import condition

from .models import Widget


def last_modified_widget_output(request, project_id, dashboard_id, pk):
    widget = Widget.objects.get(pk=pk)
    widget_update = (
        max(widget.updated, widget.table.data_updated, widget.page.dashboard.updated)
        if widget.table
        else widget.updated
    )
    if widget.page.has_control and widget.date_column:
        return max(widget_update, widget.page.control.updated)
    return widget_update


def etag_widget_output(request, project_id, dashboard_id, pk):
    last_modified = last_modified_widget_output(request, project_id, dashboard_id, pk)
    return str(int(last_modified.timestamp() * 1_000_000))


# No cache header tells browser to always re-validate the resource
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching#controlling_caching
# https://web.dev/http-cache/#flowchart
widget_output = lambda view: cache_control(no_cache=True)(
    condition(
        etag_func=etag_widget_output, last_modified_func=last_modified_widget_output
    )(view)
)
