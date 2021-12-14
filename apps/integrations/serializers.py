from rest_framework import serializers

from apps.runs.serializers import JobRunSerializer

from .models import Integration


class IntegrationSerializer(serializers.ModelSerializer):
    absolute_url = serializers.URLField(source="get_absolute_url", read_only=True)
    latest_run = JobRunSerializer()

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
            "automate_node_id",
            "connector",
            "sheet",
            "upload",
            "absolute_url",
            "icon",
            "latest_run",
        )
