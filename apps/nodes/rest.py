import json

import coreapi
from apps.base.analytics import NODE_CONNECTED_EVENT, NODE_CREATED_EVENT, track_node
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import api_view, schema
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema

from .models import NODE_CONFIG, Node
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
            # Explicitly update node when parents are updated
            node.data_updated = timezone.now()
            node.save()


@api_view(http_method_names=["POST"])
def duplicate_node(request, pk):
    node = get_object_or_404(Node, pk=pk)
    clone = node.make_clone(
        attrs={
            "name": "Copy of " + (node.name or NODE_CONFIG[node.kind]["displayName"]),
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
def update_positions(request, pk):
    ids = [d["id"] for d in request.data]
    nodes = Node.objects.filter(id__in=ids)
    for node in nodes:
        position = next(filter(lambda x: x["id"] == str(node.id), request.data))
        node.x = position["x"]
        node.y = position["y"]
    Node.objects.bulk_update(nodes, ["x", "y"])
    return Response({}, status=200)
