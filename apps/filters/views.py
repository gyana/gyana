import ibis.expr.datatypes as dt
from apps.widgets.models import Widget
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .models import Filter


@api_view(http_method_names=["GET"])
def autocomplete_options(request, pk):
    """
    Receives a query and returns a list of values
    """
    q = request.GET["q"].lower()
    # We have to provide the selected column via the request
    # Because it's only set on the filter_ object after saving
    column = request.GET["column"]

    filter_ = get_object_or_404(Filter, pk=pk)
    source = filter_.widget or filter_.node.parents.first()
    query = (source.table if isinstance(source, Widget) else source).get_query()

    options = (
        query[query[column].cast(dt.String()).lower().startswith(q)]
        .projection([column])
        .distinct()
        # For now simply limit the results to 20
        # Later we could also make the list scrollable
        # and send in chunks
        .limit(20)
        .execute()
        .values.flatten()
        .tolist()
    )
    return Response(options)
