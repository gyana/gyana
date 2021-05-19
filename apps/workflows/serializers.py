from rest_framework import serializers

from .models import Column, Node, Workflow


class NodeSerializer(serializers.ModelSerializer):

    workflow = serializers.PrimaryKeyRelatedField(queryset=Workflow.objects.all())

    class Meta:
        model = Node
        fields = ("id", "kind", "x", "y", "workflow", "parents")


class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ["name"]


class NodeConfigSerializer(serializers.ModelSerializer):
    columns = ColumnSerializer(many=True)

    class Meta:
        model = Node
        exclude = ("id", "kind", "x", "y", "workflow", "parents")
