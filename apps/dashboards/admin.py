from apps.widgets.admin import WidgetInline
from django.contrib import admin

from .models import Dashboard


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "project", "shared_status"]
    fields = ["id", "name", "project", "shared_status"]
    readonly_fields = ["id"]
    inlines = [WidgetInline]

    def has_add_permission(self, request):
        return False
