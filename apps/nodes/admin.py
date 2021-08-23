from django.contrib import admin
from django.utils.html import format_html

from .models import Node


class NodeInline(admin.TabularInline):
    model = Node
    fields = ["id", "name", "kind", "error", "bq_dashboard_url"]
    readonly_fields = ["id", "name", "kind", "error", "bq_dashboard_url"]
    extra = 0

    def bq_dashboard_url(self, instance):
        return format_html(
            '<a href="{0}" target="_blank">{1}</a>',
            instance.table.bq_dashboard_url,
            "Link",
        )

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj):
        return False
