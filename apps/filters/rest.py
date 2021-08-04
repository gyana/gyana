import ibis.expr.datatypes as dt
from apps.nodes.bigquery import get_query_from_node
from apps.nodes.models import Node
from apps.widgets.models import Widget
from apps.utils.clients import get_dataframe
from apps.tables.bigquery import get_query_from_table
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response


@api_view(http_method_names=["GET"])
def autocomplete_options(request):
    """
    Receives a query and returns a list of values
    """

    q = request.GET["q"].lower()
    # We have to provide the selected column via the request
    # Because it's only set on the filter_ object after saving
    column = request.GET["column"]

    # Instead of using the filter we need to use send the parent via the request
    # For filters that are just being created and can't be fetched
    # from the DB yet
    parent = (
        get_object_or_404(Widget, pk=request.GET["parentId"]).table
        if request.GET["parentType"] == "widget"
        else get_object_or_404(Node, pk=request.GET["parentId"])
    )
    query = (
        get_query_from_table(parent)
        if request.GET["parentType"] == "widget"
        else get_query_from_node(parent)
    )

    options = (
        get_dataframe(
            query[query[column].cast(dt.String()).lower().startswith(q)]
            .projection([column])
            .distinct()
            # For now simply limit the results to 20
            # Later we could also make the list scrollable
            # and send in chunks
            .limit(20)
            .compile()
        )
        .values.flatten()
        .tolist()
    )
    return Response(options)
