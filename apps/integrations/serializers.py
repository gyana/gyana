from rest_framework import serializers

from .models import Integration

# from apps.connectors.serializers import ConnectorSerializer
# from apps.sheets.serializers import SheetSerializer
# from apps.uploads.models import Upload


# class UploadSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Upload
#         fields = ("id",)


class IntegrationSerializer(serializers.ModelSerializer):
    # connector = ConnectorSerializer()
    # sheet = SheetSerializer()
    # upload = UploadSerializer()
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
