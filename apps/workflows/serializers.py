from rest_framework import serializers

from apps.nodes.models import Node
from apps.runs.serializers import JobRunSerializer

from .models import Workflow


class WorkflowSerializer(serializers.ModelSerializer):
    parents = serializers.SerializerMethodField()
    latest_run = JobRunSerializer()
    absolute_url = serializers.URLField(source="get_absolute_url", read_only=True)

    class Meta:
        model = Workflow
        fields = (
            "id",
            "name",
            "entity_id",
            "parents",
            "absolute_url",
            "latest_run",
        )

    def get_parents(self, obj):
        parents = {
            node.input_table.source_obj
            for node in obj.nodes.filter(
                kind=Node.Kind.INPUT, input_table__isnull=False
            )
        }
        return [source.entity_id for source in parents]
