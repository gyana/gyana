from rest_framework import serializers

from .models import Node, Workflow


class NodeSerializer(serializers.ModelSerializer):

    workflow = serializers.PrimaryKeyRelatedField(queryset=Workflow.objects.all())
    description = serializers.SerializerMethodField()

    class Meta:
        model = Node
        fields = ("id", "kind", "x", "y", "workflow", "parents", "description")

    def get_description(self, obj):
        return (
            f"limit {obj.limit_limit} offset {obj.limit_offset}"
            if obj.kind == obj.Kind.LIMIT
            else "TODO"
        )
