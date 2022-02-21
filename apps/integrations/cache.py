from django.views.decorators.cache import cache_control
from django.views.decorators.http import condition


from .models import Integration


def last_modified_integration_grid(request, pk):
    integration = Integration.objects.get(pk=pk)
    table_id = request.GET.get("table_id")
    table_instance = integration.get_table_by_pk_safe(table_id)
    return table_instance.data_updated


def etag_integration_grid(request, pk):
    last_modified = last_modified_integration_grid(request, pk)
    return str(int(last_modified.timestamp() * 1_000_000))


# See widgets/cache.py
integration_grid = lambda view: cache_control(no_cache=True)(
    condition(
        etag_func=etag_integration_grid,
        last_modified_func=last_modified_integration_grid,
    )(view)
)
