from django.contrib import admin

from apps.widgets.admin import WidgetInline

from .models import Dashboard, Page


class PageInline(admin.TabularInline):
    model = Page
    fields = ["id", "position"]
    extra = 0


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "project", "shared_status"]
    fields = ["id", "name", "project", "shared_status"]
    readonly_fields = ["id"]
    inlines = [PageInline]

    def has_add_permission(self, request):
        return False
