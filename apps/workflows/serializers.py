from rest_framework import serializers

from apps.nodes.models import Node
from apps.tables.models import Table

from .models import Workflow


class WorkflowSerializer(serializers.ModelSerializer):
    parents = serializers.SerializerMethodField()

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
            "parents",
        )

    def get_parents(self, obj):
        return [
            node.input_table.workflow_node.workflow_id
            for node in obj.nodes.filter(
                kind=Node.Kind.INPUT, input_table__source=Table.Source.WORKFLOW_NODE
            )
        ]
