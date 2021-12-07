from rest_framework import serializers

from apps.sheets.models import Sheet


class SheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sheet
        fields = (
            "id",
            "is_scheduled",
            "failed_at",
            "schedule_status",
            "run_status",
            "up_to_date",
        )
