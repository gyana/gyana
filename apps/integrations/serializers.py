from rest_framework import serializers

from .models import Integration


class IntegrationSerializer(serializers.ModelSerializer):
    schedule_node_id = serializers.SerializerMethodField()

    class Meta:
        model = Integration
        fields = (
            "id",
            "project",
            "kind",
            "name",
            "state",
            "ready",
            "created_ready",
            "created_by",
            "schedule_node_id",
        )

    def get_schedule_node_id(self, obj):
        return f"{obj._meta.db_table}-{obj.id}"
