from apps.nodes.admin import NodeInline
from django.contrib import admin

from .models import Workflow


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "project", "last_run")
    fields = ["id", "name", "project", "last_run"]
    readonly_fields = ["id", "last_run"]
    inlines = [NodeInline]

    def has_add_permission(self, request):
        return False
