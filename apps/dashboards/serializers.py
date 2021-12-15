from rest_framework import serializers

from .models import Dashboard


class DashboardSerializer(serializers.ModelSerializer):
    parents = serializers.SerializerMethodField()
    absolute_url = serializers.URLField(source="get_absolute_url", read_only=True)

    class Meta:
        model = Dashboard
        fields = (
            "id",
            "name",
            "entity_id",
            "parents",
            "absolute_url",
        )

    def get_parents(self, obj):
        parents = {
            widget.table.source_obj
            for widget in obj.widgets.filter(table__isnull=False).all()
        }
        return [source.entity_id for source in parents]
