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
            "kind",
            "name",
            "state",
            "entity_id",
            "absolute_url",
            "icon",
            "latest_run",
        )
