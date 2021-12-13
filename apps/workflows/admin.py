from django.contrib import admin

from apps.nodes.admin import NodeInline

from .models import Workflow


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "project")
    fields = ["id", "name", "project"]
    readonly_fields = ["id"]
    inlines = [NodeInline]

    def has_add_permission(self, request):
        return False
