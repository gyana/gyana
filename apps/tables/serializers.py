import json

from django.templatetags.static import static
from rest_framework import serializers

from .models import Table


class TableSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = [
            "id",
            "image",
            "owner_name",
            "out_of_date",
        ]

    def get_image(self, obj):
        return static(obj.integration.icon) if obj.integration else None


class TableSchemaSerializer(serializers.ModelSerializer):
    schema_json = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = ["id", "schema"]

    def get_schema_json(self, obj):
        return json.dumps({c: obj.schema[c].name for c in obj.schema})
