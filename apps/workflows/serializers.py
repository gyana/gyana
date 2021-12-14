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
            "project",
            "last_success_run",
            "data_updated",
            "is_scheduled",
            # "succeeded_at",
            # "failed_at",
            "schedule_node_id",
            "parents",
            "absolute_url",
            # "schedule_status",
            # "run_status",
            # "up_to_date",
            "latest_run",
        )

    def get_parents(self, obj):
        parents = {
            node.input_table.source_obj
            for node in obj.nodes.filter(
                kind=Node.Kind.INPUT, input_table__isnull=False
            )
        }
        return [source.schedule_node_id for source in parents]
