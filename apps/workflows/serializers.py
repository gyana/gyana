from rest_framework import serializers

from .models import Workflow, Node


class NodeSerializer(serializers.ModelSerializer):

    workflow = serializers.PrimaryKeyRelatedField(queryset=Workflow.objects.all())

    class Meta:
        model = Node
        fields = ("id", "kind", "x", "y", "workflow", "parents")
