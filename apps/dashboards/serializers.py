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
            "automate_node_id",
            "parents",
            "absolute_url",
        )

    def get_parents(self, obj):
        parents = {widget.table.source_obj for widget in obj.get_all_widgets()}
        return [source.automate_node_id for source in parents]
