from django.contrib import admin


from .models import Dashboard, Page


class PageInline(admin.TabularInline):
    model = Page
    fields = ["id", "position"]
    extra = 0


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "project", "shared_status"]
    search_fields = ["id", "name", "project__name"]
    readonly_fields = ["id", "project"]
    fields = readonly_fields + ["name", "shared_status"]

    inlines = [PageInline]

    def has_add_permission(self, request):
        return False
