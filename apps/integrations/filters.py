import django_filters
from django import forms
from django.db import models

from .models import Integration


class IntegrationFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        lookup_expr="icontains",
        widget=forms.TextInput(attrs={"placeholder": "Search by name..."}),
    )

    class Meta:
        model = Integration
        fields = ["name", "kind"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["kind"].field.empty_label = "All sources"
