from rest_framework import serializers

from apps.nodes.models import Node

from .models import Workflow


class WorkflowSerializer(serializers.ModelSerializer):
    schedule_node_id = serializers.SerializerMethodField()
    parents = serializers.SerializerMethodField()
    absolute_url = serializers.URLField(source="get_absolute_url", read_only=True)

    class Meta:
        model = Workflow
        fields = (
            "id",
            "name",
            "project",
            "last_run",
            "data_updated",
            "is_scheduled",
            "succeeded_at",
            "failed_at",
            "schedule_node_id",
            "parents",
            "absolute_url",
        )

    def get_schedule_node_id(self, obj):
        return f"{obj._meta.db_table}-{obj.id}"

    def get_parents(self, obj):
        parents = [
            node.input_table.source_obj
            for node in obj.nodes.filter(kind=Node.Kind.INPUT)
        ]
        return [f"{source._meta.db_table}-{source.id}" for source in parents]
