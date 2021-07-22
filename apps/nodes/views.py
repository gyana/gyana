import json
from functools import cached_property

import coreapi
from apps.utils.formset_update_view import FormsetUpdateView
from apps.utils.segment_analytics import (
    NODE_CONNECTED_EVENT,
    NODE_CREATED_EVENT,
    NODE_UPDATED_EVENT,
    track_node,
)
from apps.utils.table_data import get_table
from django import forms, template
from django.http.response import HttpResponse
from django.urls import reverse
from django.views.generic.base import TemplateView
from django_tables2.config import RequestConfig
from django_tables2.tables import Table
from django_tables2.views import SingleTableMixin
from rest_framework import viewsets
from rest_framework.decorators import api_view, schema
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from turbo_response.views import TurboUpdateView

from .forms import KIND_TO_FORM
from .formsets import KIND_TO_FORMSETS
from .models import Node, NodeConfig
from .serializers import NodeSerializer


class NodeViewSet(viewsets.ModelViewSet):
    serializer_class = NodeSerializer
    filterset_fields = ["workflow"]

    # Overwriting queryset to prevent access to nodes that don't belong to
    # the user's team
    def get_queryset(self):
        # To create schema this is called without a request
        if self.request is None:
            return Node.objects.all()
        return Node.objects.filter(
            workflow__project__team__in=self.request.user.teams.all()
        ).all()

    def perform_create(self, serializer):
        node: Node = serializer.save()
        track_node(self.request.user, node, NODE_CREATED_EVENT)

    def perform_update(self, serializer):
        node: Node = serializer.save()

        # if the parents get updated we know the user is connecting nodes to eachother
        if "parents" in self.request.data:
            track_node(
                self.request.user,
                node,
                NODE_CONNECTED_EVENT,
                parent_ids=json.dumps(list(node.parents.values_list("id", flat=True))),
                parent_kinds=json.dumps(
                    list(node.parents.values_list("kind", flat=True))
                ),
            )


class NodeName(TurboUpdateView):
    model = Node
    fields = ("name",)
    template_name = "nodes/name.html"

    def get_success_url(self) -> str:
        return reverse(
            "nodes:name",
            args=(self.object.id,),
        )


class NodeUpdate(FormsetUpdateView):
    template_name = "nodes/update.html"
    model = Node

    @cached_property
    def formsets(self):
        return KIND_TO_FORMSETS.get(self.object.kind, [])

    def get_formset_kwargs(self, formset):

        if formset.get_default_prefix() in [
            "add_columns",
            "edit_columns",
            "aggregations",
            "filters",
            "formula_columns",
            "window_columns",
        ]:
            return {"schema": self.object.parents.first().schema}

        return {}

    @property
    def preview_node_id(self):
        return int(self.request.GET.get("preview_node_id", self.object.id))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workflow"] = self.object.workflow
        context["preview_node_id"] = self.preview_node_id
        context["show_docs"] = self.request.GET.get("show_docs", False) == "true" or (
            self.object.data_updated is None
            and self.object.kind not in ["union", "intersect"]
        )
        help_template = f"nodes/help/{self.object.kind}.html"
        context["help_template"] = (
            help_template
            if template_exists(help_template)
            else "nodes/help/default.html"
        )

        # Add node type to list if it requires live updates
        context["do_live_updates"] = self.object.kind in [
            "pivot",
            "add",
            "edit",
            "aggregation",
            "filter",
            "unpivot",
            "window",
        ]
        return context

    def get_form_class(self):
        return KIND_TO_FORM[self.object.kind]

    def form_valid(self, form: forms.Form) -> HttpResponse:
        r = super().form_valid(form)
        track_node(self.request.user, form.instance, NODE_UPDATED_EVENT)
        return r

    def get_success_url(self) -> str:
        base_url = reverse("nodes:update", args=(self.object.id,))

        if self.request.POST.get("submit") == "Save & Preview":
            return f"{base_url}?preview_node_id={self.preview_node_id}"

        return base_url


def template_exists(template_name):
    try:
        template.loader.get_template(template_name)
        return True
    except template.TemplateDoesNotExist:
        return False


class NodeGrid(SingleTableMixin, TemplateView):
    template_name = "nodes/grid.html"
    paginate_by = 15

    def get_context_data(self, **kwargs):
        self.node = Node.objects.get(id=kwargs["pk"])
        context = super().get_context_data(**kwargs)
        context["node"] = self.node
        error_template = f"nodes/errors/{self.node.kind}.html"
        if template_exists(error_template):
            context["error_template"] = error_template
        return context

    def get_table(self, **kwargs):
        try:
            table = get_table(self.node.schema, self.node.get_query(), **kwargs)

            return RequestConfig(
                self.request, paginate=self.get_table_pagination(table)
            ).configure(table)
        except Exception as err:
            # We have to return
            return type("DynamicTable", (Table,), {})(data=[])


@api_view(http_method_names=["POST"])
def duplicate_node(request, pk):
    node = get_object_or_404(Node, pk=pk)
    clone = node.make_clone(
        attrs={
            "name": "Copy of " + (node.name or NodeConfig[node.kind]["displayName"]),
            "x": node.x + 50,
            "y": node.y + 50,
        }
    )

    # Add more M2M here if necessary
    for parent in node.parents.iterator():
        clone.parents.add(parent)
    return Response(NodeSerializer(clone).data)


@api_view(http_method_names=["POST"])
@schema(
    AutoSchema(
        manual_fields=[
            coreapi.Field(
                name="nodes",
                required=True,
                location="body",
                description="List of node ids and position to update",
            ),
        ]
    )
)
def update_positions(request, workflow_id):
    ids = [d["id"] for d in request.data]
    nodes = Node.objects.filter(id__in=ids)
    for node in nodes:
        position = next(filter(lambda x: x["id"] == str(node.id), request.data))
        node.x = position["x"]
        node.y = position["y"]
    Node.objects.bulk_update(nodes, ["x", "y"])
    return Response({}, status=200)
