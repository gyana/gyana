from rest_framework import serializers

from .models import Dashboard


class DashboardSerializer(serializers.ModelSerializer):
    schedule_node_id = serializers.SerializerMethodField()
    parents = serializers.SerializerMethodField()
    absolute_url = serializers.URLField(source="get_absolute_url", read_only=True)

    class Meta:
        model = Dashboard
        fields = (
            "id",
            "name",
            "project",
            "shared_status",
            "schedule_node_id",
            "parents",
            "absolute_url",
        )

    def get_schedule_node_id(self, obj):
        return f"{obj._meta.db_table}-{obj.id}"

    def get_parents(self, obj):
        parents = {widget.table.source_obj for widget in obj.widget_set.all()}
        return [self.get_schedule_node_id(source) for source in parents]
