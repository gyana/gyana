import ibis.expr.datatypes as dt
from apps.base.clients import get_dataframe
from apps.nodes.bigquery import get_query_from_node
from apps.nodes.models import Node
from apps.tables.bigquery import get_query_from_table
from apps.teams.roles import user_can_access_team
from apps.widgets.models import Widget
from django.http import Http404
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
    parentType = request.GET["parentType"]
    parent = (
        get_object_or_404(Widget, pk=request.GET["parentId"]).table
        if parentType == "widget"
        else get_object_or_404(Node, pk=request.GET["parentId"])
    )
    if (
        parentType == "widget"
        and user_can_access_team(request.user, parent.dashboard.project.team)
        or (
            parentType == "node"
            and user_can_access_team(request.user, parent.workflow.project.team)
        )
    ):
        query = (
            get_query_from_table(parent)
            if parentType == "widget"
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

    raise Http404
