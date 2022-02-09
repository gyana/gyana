from django.contrib import admin

from apps.nodes.admin import NodeInline

from .models import Workflow


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "project", "last_success_run")
    search_fields = ["id", "name", "project__name"]
    readonly_fields = ["id", "project", "last_success_run"]
    fields = readonly_fields + ["name"]

    inlines = [NodeInline]

    def has_add_permission(self, request):
        return False
