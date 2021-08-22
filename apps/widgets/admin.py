from django.contrib import admin
from django.utils.html import format_html

from .models import Widget


class WidgetInline(admin.TabularInline):
    model = Widget
    fields = ["id", "name", "kind", "bq_dashboard_url", "is_valid"]
    readonly_fields = ["id", "name", "kind", "bq_dashboard_url", "is_valid"]
    extra = 0

    def bq_dashboard_url(self, instance):
        return format_html(
            '<a href="{0}" target="_blank">{1}</a>',
            instance.table.bq_dashboard_url,
            "Link",
        )

    @admin.display(boolean=True)
    def is_valid(self, instance):
        return instance.is_valid

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj):
        return False
