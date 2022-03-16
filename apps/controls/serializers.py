from rest_framework import serializers

from .models import ControlWidget


class ControlWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlWidget
        fields = ("id", "x", "y", "width", "height")
