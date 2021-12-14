from rest_framework import serializers

from .models import JobRun


class JobRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRun
        fields = (
            "id",
            "state",
            "started_at",
            "completed_at",
        )
