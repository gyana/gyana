from rest_framework import serializers

from .models import Dataflow, Node


class NodeSerializer(serializers.ModelSerializer):

    dataflow = serializers.PrimaryKeyRelatedField(queryset=Dataflow.objects.all())

    class Meta:
        model = Node
        fields = ("id", "kind", "x", "y", "dataflow", "parents")
