from rest_framework import serializers
import json
from .models import Table


class TableSerializer(serializers.ModelSerializer):
    schema_json = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = (
            "id",
            "schema_json",
        )

    def get_schema_json(self, obj):
        return json.dumps({c: obj.schema[c].name for c in obj.schema})
