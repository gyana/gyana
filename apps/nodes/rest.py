import coreapi
from rest_framework import viewsets
from rest_framework.decorators import api_view, schema
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema

from apps.base.analytics import (
    NODE_CONNECTED_EVENT,
    NODE_CREATED_EVENT,
    track_edge,
    track_node,
)

from .models import NODE_CONFIG, Edge, Node
from .serializers import EdgeSerializer, NodeSerializer


class EdgeViewSet(viewsets.ModelViewSet):
    serializer_class = EdgeSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Edge.objects.filter(
            parent__workflow__project__team__members=self.request.user
        ).all()

    def perform_create(self, serializer):
        edge: Edge = serializer.save()
        track_edge(self.request.user, edge, NODE_CONNECTED_EVENT)

    def perform_update(self, serializer):
        edge: Edge = serializer.save()
        track_edge(self.request.user, edge, NODE_CONNECTED_EVENT)


class NodeViewSet(viewsets.ModelViewSet):
    serializer_class = NodeSerializer
    filterset_fields = ["workflow"]
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # to create the DRF schema this is called without a request
        if self.request is None:
            return Node.objects.none()
        return Node.objects.filter(
            workflow__project__team__members=self.request.user
        ).all()

    def perform_create(self, serializer):
        node: Node = serializer.save()
        track_node(self.request.user, node, NODE_CREATED_EVENT)


@api_view(http_method_names=["POST"])
def duplicate_node(request, pk):
    node = get_object_or_404(Node, pk=pk)
    clone = node.make_clone(
        attrs={
            "name": "Copy of " + (node.name or NODE_CONFIG[node.kind]["displayName"]),
            # Magic numbers: A multiple of GRID_GAP found in DnDFlow.tsx
            "x": node.x + 80,
            "y": node.y + 80,
        }
    )

    # Add more M2M here if necessary
    for parent in node.parent_edges.iterator():
        clone.parents.add(parent.parent, through_defaults={"position": parent.position})
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
