import ibis.expr.datatypes as dt
from django.http import Http404
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.base.clients import get_engine
from apps.nodes.engine import get_query_from_node
from apps.nodes.models import Node
from apps.projects.access import user_can_access_project
from apps.widgets.models import Widget


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
        get_object_or_404(Widget, pk=request.GET["parentId"])
        if parentType == "widget"
        else get_object_or_404(Node, pk=request.GET["parentId"])
    )
    if (
        parentType == "widget"
        and user_can_access_project(request.user, parent.page.dashboard.project)
        or (
            parentType == "node"
            and user_can_access_project(request.user, parent.workflow.project)
        )
    ):
        # For widgets we are sending the table information
        # To make sure we always have the correct one
        # For nodes we actually want the parent of the parent

        query = (
            get_engine().get_table(parent.table)
            if parentType == "widget"
            else get_query_from_node(parent.parents.first())
        )

        options = [
            row[column]
            for row in (
                query[query[column].cast(dt.String()).lower().startswith(q)]
                .projection([column])
                .distinct()
                # For now simply limit the results to 20
                # Later we could also make the list scrollable
                # and send in chunks
                .limit(20)
                .execute()
                .to_dict(orient="records")
            )
        ]
        return Response(options)

    raise Http404
