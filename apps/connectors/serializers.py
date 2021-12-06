from rest_framework import serializers

from apps.connectors.models import Connector


class ConnectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connector
        fields = ("id", "is_scheduled", "failed_at", "schedule_status", "up_to_date")
