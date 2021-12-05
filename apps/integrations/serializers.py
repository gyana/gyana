from rest_framework import serializers

from apps.connectors.models import Connector
from apps.sheets.models import Sheet
from apps.uploads.models import Upload

from .models import Integration


class ConnectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connector
        fields = ("id", "is_scheduled", "failed_at")


class SheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sheet
        fields = ("id", "is_scheduled", "failed_at")


class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = ("id",)


class IntegrationSerializer(serializers.ModelSerializer):
    schedule_node_id = serializers.SerializerMethodField()
    connector = ConnectorSerializer()
    sheet = SheetSerializer()
    upload = UploadSerializer()
    absolute_url = serializers.URLField(source="get_absolute_url", read_only=True)

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
            "connector",
            "sheet",
            "upload",
            "absolute_url",
            "icon",
        )

    def get_schedule_node_id(self, obj):
        return f"{obj._meta.db_table}-{obj.id}"
