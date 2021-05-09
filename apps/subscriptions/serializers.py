from djstripe.models import Product, Plan
from rest_framework import serializers


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ('id', 'name')


class PlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plan
        fields = ('id', 'nickname', 'amount')
