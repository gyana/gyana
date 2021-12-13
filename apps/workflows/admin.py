from django.contrib import admin

from apps.nodes.admin import NodeInline

from .models import Workflow


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "project", "last_success_run")
    fields = ["id", "name", "project", "last_success_run"]
    readonly_fields = ["id", "last_success_run"]
    inlines = [NodeInline]

    def has_add_permission(self, request):
        return False
